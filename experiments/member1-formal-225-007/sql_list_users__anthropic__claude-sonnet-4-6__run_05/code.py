import sqlite3

def list_users(conn: sqlite3.Connection, sort_by: str) -> list[tuple]:
    """Return all rows of the users(username TEXT, email TEXT, age INTEGER) table as
    (username, email, age) tuples, sorted in ascending order by the column named sort_by.
    Do not commit or close the connection.
    """
    allowed_columns = {"username", "email", "age"}
    if sort_by not in allowed_columns:
        raise ValueError(f"Invalid sort_by column: {sort_by!r}. Must be one of {allowed_columns}")
    
    cursor = conn.cursor()
    cursor.execute(f"SELECT username, email, age FROM users ORDER BY {sort_by} ASC")
    return cursor.fetchall()
