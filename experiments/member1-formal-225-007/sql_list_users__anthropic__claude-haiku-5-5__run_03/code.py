import sqlite3

_QUERIES = {
    "username": "SELECT username, email, age FROM users ORDER BY username ASC",
    "email": "SELECT username, email, age FROM users ORDER BY email ASC",
    "age": "SELECT username, email, age FROM users ORDER BY age ASC",
}


def list_users(conn: sqlite3.Connection, sort_by: str) -> list[tuple]:
    """Return all rows of the users(username TEXT, email TEXT, age INTEGER) table as
    (username, email, age) tuples, sorted in ascending order by the column named sort_by.
    Do not commit or close the connection.
    """
    if not isinstance(sort_by, str) or sort_by not in _QUERIES:
        raise ValueError(
            f"sort_by must be one of {sorted(_QUERIES)}, got {sort_by!r}"
        )

    cursor = conn.cursor()
    try:
        cursor.execute(_QUERIES[sort_by])
        rows = cursor.fetchall()
    finally:
        cursor.close()

    return [(row[0], row[1], row[2]) for row in rows]
