import sqlite3

_ALLOWED_COLUMNS = {
    "username": "username",
    "email": "email",
    "age": "age",
}


def list_users(conn: sqlite3.Connection, sort_by: str) -> list[tuple]:
    """Return all rows of the users(username TEXT, email TEXT, age INTEGER) table as
    (username, email, age) tuples, sorted in ascending order by the column named sort_by.
    Do not commit or close the connection.
    """
    if not isinstance(sort_by, str) or sort_by not in _ALLOWED_COLUMNS:
        raise ValueError("Invalid sort column")
    column = _ALLOWED_COLUMNS[sort_by]
    query = f"SELECT username, email, age FROM users ORDER BY {column} ASC"
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        return [tuple(row) for row in cursor.fetchall()]
    finally:
        cursor.close()
