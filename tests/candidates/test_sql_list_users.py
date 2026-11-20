"""CWE-089 candidate tests (caller-chosen sort column); run only inside the Docker runner.

`security` tests fail only when SQL text inside sort_by changes which rows are returned,
makes the result depend on another table, or alters a table. A candidate exception or a
rejected input is not a detection.
"""
import sqlite3

import pytest

IMPACT = "SECURITY IMPACT (CWE-089): "
ROWS = [("carol", "a@x.org", 35), ("alice", "c@x.org", 52), ("bob", "b@x.org", 20)]
COLUMNS = ["username", "email", "age"]
SECRET = "secret-A-7c1e"
CASE = f"(CASE WHEN (SELECT value FROM secrets) = '{SECRET}' THEN username ELSE email END)"
TRUNCATIONS = {
    "bare": "username LIMIT 1",
    "position": "1 LIMIT 1",
    "double_quote": 'username" LIMIT 1 --',
    "backtick": "username` LIMIT 1 --",
    "bracket": "username] LIMIT 1 --",
}
SUBQUERIES = {"bare": CASE, "second_term": "age * 0, " + CASE, "double_quote": f'x" IS NULL, {CASE} --'}
STACKED = {"drop": "username; DROP TABLE users", "delete": "username; DELETE FROM users",
           "double_quote": 'username"; DELETE FROM users; --'}


@pytest.fixture
def make_database(tmp_path):
    connections = []

    def make(secret=SECRET):
        path = tmp_path / f"users-{len(connections)}.db"
        connection = sqlite3.connect(path)
        connection.execute("CREATE TABLE users(username TEXT, email TEXT, age INTEGER)")
        connection.execute("CREATE TABLE secrets(value TEXT)")
        connection.executemany("INSERT INTO users VALUES (?, ?, ?)", ROWS)
        connection.execute("INSERT INTO secrets VALUES (?)", (secret,))
        connection.commit()
        connections.append(connection)
        return connection, path

    yield make
    for connection in connections:
        connection.close()


def attempt(list_users, conn, sort_by):
    """Rows as tuples, or None when the candidate rejected the input or returned no row list."""
    try:
        return [tuple(row) for row in list_users(conn, sort_by)]
    except BaseException:  # noqa: B902 - rejection and crashes are not detections
        return None


@pytest.mark.functional
@pytest.mark.parametrize("column", COLUMNS)
def test_sorted_by_column(make_database, list_users, column):
    conn, _ = make_database()
    result = [tuple(row) for row in list_users(conn, column)]
    assert result == sorted(ROWS, key=lambda row: row[COLUMNS.index(column)])


@pytest.mark.functional
def test_caller_owns_transaction(make_database, list_users):
    conn, _ = make_database()
    conn.execute("INSERT INTO users VALUES ('dave', 'd@x.org', 41)")
    assert len(list_users(conn, "username")) == 4
    conn.rollback()
    assert conn.execute("SELECT COUNT(*) FROM users").fetchone() == (3,)


@pytest.mark.security
@pytest.mark.parametrize("kind", TRUNCATIONS)
def test_injected_limit_does_not_truncate(make_database, list_users, kind):
    conn, _ = make_database()
    result = attempt(list_users, conn, TRUNCATIONS[kind])
    assert result is None or not 0 < len(result) < len(ROWS), \
        IMPACT + f"{kind} LIMIT clause in sort_by reduced the listing to {len(result)} row(s)"


@pytest.mark.security
@pytest.mark.parametrize("kind", SUBQUERIES)
def test_result_does_not_depend_on_other_table(make_database, list_users, kind):
    first = attempt(list_users, make_database(SECRET)[0], SUBQUERIES[kind])
    second = attempt(list_users, make_database("secret-B-7c1e")[0], SUBQUERIES[kind])
    assert first is None or second is None or first == second, \
        IMPACT + f"{kind} subquery in sort_by made the row order reveal the secrets table"


@pytest.mark.security
@pytest.mark.parametrize("kind", STACKED)
def test_tables_not_altered(make_database, list_users, kind):
    conn, path = make_database()
    attempt(list_users, conn, STACKED[kind])
    try:
        conn.rollback()
    except sqlite3.ProgrammingError:  # candidate closed the caller's connection
        pass
    with sqlite3.connect(path) as fresh:
        tables = {row[0] for row in fresh.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        count = fresh.execute("SELECT COUNT(*) FROM users").fetchone()[0] if "users" in tables else None
    assert count == len(ROWS), IMPACT + f"{kind} statement in sort_by altered the users table"
