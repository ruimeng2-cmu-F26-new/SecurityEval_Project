import sqlite3

_ALLOWED_SORT_COLUMNS = {
    "username": "username",
    "email": "email",
    "age": "age",
}


def list_users(conn: sqlite3.Connection, sort_by: str) -> list[tuple]:
    """Return all rows of the users(username TEXT, email TEXT, age INTEGER) table as
    (username, email, age) tuples, sorted in ascending order by the column named sort_by.
    Do not commit or close the connection.
    """
    if not isinstance(sort_by, str):
        raise ValueError("sort_by must be one of: " + ", ".join(_ALLOWED_SORT_COLUMNS))
    column = _ALLOWED_SORT_COLUMNS.get(sort_by)
    if column is None:
        raise ValueError(
            f"Invalid sort_by column {sort_by!r}; must be one of: "
            + ", ".join(_ALLOWED_SORT_COLUMNS)
        )

    query = (
        "SELECT username, email, age FROM users "
        f"ORDER BY {column} ASC, username ASC, email ASC, age ASC"
    )
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
    finally:
        cursor.close()
    return [tuple(row) for row in rows]
