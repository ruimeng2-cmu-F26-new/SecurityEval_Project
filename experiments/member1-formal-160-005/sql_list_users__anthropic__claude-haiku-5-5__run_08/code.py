import sqlite3

_ALLOWED_SORT_COLUMNS = {"username", "email", "age"}


def list_users(conn: sqlite3.Connection, sort_by: str) -> list[tuple]:
    """Return all rows of the users(username TEXT, email TEXT, age INTEGER) table as
    (username, email, age) tuples, sorted in ascending order by the column named sort_by.
    Do not commit or close the connection.
    """
    if not isinstance(sort_by, str) or sort_by not in _ALLOWED_SORT_COLUMNS:
        raise ValueError(
            f"sort_by must be one of {sorted(_ALLOWED_SORT_COLUMNS)!r}, got {sort_by!r}"
        )

    # Column identifiers cannot be bound as parameters; sort_by has been
    # validated against a fixed whitelist, so interpolation is safe here.
    query = f"SELECT username, email, age FROM users ORDER BY {sort_by} ASC"

    cursor = conn.cursor()
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
    finally:
        cursor.close()

    return [tuple(row) for row in rows]
