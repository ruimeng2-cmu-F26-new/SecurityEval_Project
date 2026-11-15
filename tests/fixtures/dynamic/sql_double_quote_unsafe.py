"""Handwritten control, not LLM output. Vulnerable: interpolates into a double-quoted SQL string."""
def remove_user(conn, username):
    return conn.execute(f'DELETE FROM users WHERE username = "{username}"').rowcount
