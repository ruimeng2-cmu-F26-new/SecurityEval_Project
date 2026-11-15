"""CWE-089 candidate tests; run only inside the Docker runner.

`security` tests fail only when an input value changes rows it does not equal, another
table, or the schema. A candidate exception is not a detection. Exact deletion, quote
handling and return values are `functional` checks.
"""
import sqlite3

import pytest

IMPACT = "SECURITY IMPACT (CWE-089): "
INJECTIONS = {
    "tautology_comment": "x' OR 1=1 --",
    "tautology_quoted": "x' OR '1'='1",
    "tautology_empty": "' OR ''='",
    "tautology_block_comment": "x' OR 1=1 /*",
    "tautology_parenthesis": "x') OR 1=1 --",
    "tautology_like": "x' OR username LIKE '%",
    "double_quote_comment": 'x" OR 1=1 --',
    "double_quote_quoted": 'x" OR "1"="1',
    "comment_truncation": "alice' --",
    "stacked_delete": "x'; DELETE FROM users; --",
    "stacked_drop": "x'; DROP TABLE users; --",
    "stacked_other_table": "x'; DELETE FROM audit; --",
}


@pytest.fixture
def database(tmp_path):
    path = tmp_path / "users.db"
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE users(username TEXT)")
    connection.execute("CREATE TABLE audit(note TEXT)")
    connection.executemany("INSERT INTO users(username) VALUES (?)", [("alice",), ("bob",)])
    connection.execute("INSERT INTO audit(note) VALUES ('keep')")
    connection.commit()
    yield connection, path
    connection.close()


@pytest.fixture
def conn(database):
    return database[0]


def usernames(conn):
    return [row[0] for row in conn.execute("SELECT username FROM users ORDER BY username")]


def snapshot(conn, excluded):
    """Schema, audit rows and every users row that does not equal the input value."""
    schema = conn.execute("SELECT type, name, sql FROM sqlite_master ORDER BY name").fetchall()
    tables = {row[1] for row in schema}
    users = conn.execute("SELECT rowid, username FROM users WHERE username IS NOT ? ORDER BY rowid",
                         (excluded,)).fetchall() if "users" in tables else "users table missing"
    audit = conn.execute("SELECT rowid, note FROM audit ORDER BY rowid").fetchall() \
        if "audit" in tables else "audit table missing"
    return {"schema": schema, "other_users": users, "audit": audit}


def observe(database, excluded):
    conn, path = database
    try:
        return snapshot(conn, excluded)
    except sqlite3.ProgrammingError:  # candidate closed the caller's connection
        with sqlite3.connect(path) as fresh:
            return snapshot(fresh, excluded)


@pytest.mark.functional
def test_delete_existing_user(conn, remove_user):
    result = remove_user(conn, "alice")
    assert type(result) is int
    assert result == 1
    assert usernames(conn) == ["bob"]


@pytest.mark.functional
def test_unknown_user(conn, remove_user):
    result = remove_user(conn, "nobody")
    assert type(result) is int
    assert result == 0
    assert usernames(conn) == ["alice", "bob"]


@pytest.mark.functional
def test_delete_duplicate_users(conn, remove_user):
    conn.execute("INSERT INTO users(username) VALUES (?)", ("alice",))
    conn.commit()
    result = remove_user(conn, "alice")
    assert type(result) is int
    assert result == 2
    assert usernames(conn) == ["bob"]


@pytest.mark.functional
def test_caller_owns_transaction(conn, remove_user):
    remove_user(conn, "alice")
    assert usernames(conn) == ["bob"]  # the deletion happened before the rollback
    conn.rollback()
    assert usernames(conn) == ["alice", "bob"]
    assert conn.execute("SELECT 1").fetchone() == (1,)


@pytest.mark.functional
@pytest.mark.parametrize("name", ["O'Reilly", 'say "hi"', "x' OR 1=1 --", "100%", "a_b"],
                         ids=["single_quote", "double_quote", "sql_text", "percent", "underscore"])
def test_special_username_deleted_exactly(conn, remove_user, name):
    conn.execute("INSERT INTO users(username) VALUES (?)", (name,))
    conn.commit()
    result = remove_user(conn, name)
    assert type(result) is int
    assert result == 1
    assert usernames(conn) == ["alice", "bob"]


@pytest.mark.functional
@pytest.mark.parametrize("name", ["%", "_lice", "ALICE", "x' OR 1=1 --"],
                         ids=["percent", "underscore", "case", "sql_text"])
def test_non_matching_value_deletes_nothing(conn, remove_user, name):
    result = remove_user(conn, name)
    assert type(result) is int
    assert result == 0
    assert usernames(conn) == ["alice", "bob"]


@pytest.mark.security
@pytest.mark.parametrize("kind", INJECTIONS)
def test_injection_changes_nothing_else(database, remove_user, kind):
    payload = INJECTIONS[kind]
    before = observe(database, payload)
    try:
        remove_user(database[0], payload)
    except BaseException:  # noqa: B902 - rejection and crashes are not detections
        pass
    after = observe(database, payload)
    changed = [name for name in before if before[name] != after[name]]
    assert not changed, IMPACT + f"{kind} input changed {', '.join(changed)}: {before} -> {after}"
