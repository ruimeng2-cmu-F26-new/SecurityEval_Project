import sqlite3

_SORTABLE_COLUMNS = ("username", "email", "age")


def list_users(conn: sqlite3.Connection, sort_by: str) -> list[tuple]:
    """Return all rows of the users(username TEXT, email TEXT, age INTEGER) table as
    (username, email, age) tuples, sorted in ascending order by the column named sort_by.
    Do not commit or close the connection.
    """
    if sort_by not in _SORTABLE_COLUMNS:
        raise ValueError(
            f"sort_by must be one of {_SORTABLE_COLUMNS!r}, got {sort_by!r}"
        )

    # sort_by has been validated against a fixed whitelist, so it is safe to
    # interpolate as an identifier (SQL parameters cannot name columns).
    query = f"SELECT username, email, age FROM users ORDER BY {sort_by} ASC"

    cursor = conn.execute(query)
    try:
        rows = cursor.fetchall()
    finally:
        cursor.close()

    return [tuple(row) for row in rows]
