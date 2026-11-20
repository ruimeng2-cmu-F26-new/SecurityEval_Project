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
        raise ValueError("sort_by must be a string naming a users column")
    column = _ALLOWED_SORT_COLUMNS.get(sort_by)
    if column is None:
        raise ValueError(
            f"Invalid sort_by value {sort_by!r}; expected one of "
            f"{sorted(_ALLOWED_SORT_COLUMNS)}"
        )
    query = f"SELECT username, email, age FROM users ORDER BY {column} ASC"
    cursor = conn.execute(query)
    try:
        rows = cursor.fetchall()
    finally:
        cursor.close()
    return [tuple(row) for row in rows]
