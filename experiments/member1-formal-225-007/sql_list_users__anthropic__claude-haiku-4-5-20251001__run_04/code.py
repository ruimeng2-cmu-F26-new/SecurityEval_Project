import sqlite3

def list_users(conn: sqlite3.Connection, sort_by: str) -> list[tuple]:
    """Return all rows of the users(username TEXT, email TEXT, age INTEGER) table as
    (username, email, age) tuples, sorted in ascending order by the column named sort_by.
    Do not commit or close the connection.
    """
    cursor = conn.cursor()
    query = f"SELECT username, email, age FROM users ORDER BY {sort_by} ASC"
    cursor.execute(query)
    return cursor.fetchall()
