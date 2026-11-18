import sqlite3


def remove_user(conn: sqlite3.Connection, username: str) -> int:
    """Remove the user with the given username from the users(username TEXT) table.
    Return the number of deleted rows. Do not commit or close the connection.
    """
    cursor = conn.execute("DELETE FROM users WHERE username = ?", (username,))
    try:
        count = cursor.rowcount
    finally:
        cursor.close()
    return count if count is not None and count >= 0 else 0
