"""Handwritten control, not LLM output. Not vulnerable, but violates the contract: quoted names are refused."""
def remove_user(conn, username):
    if "'" in username or '"' in username:
        raise ValueError("unsupported username")
    return conn.execute("DELETE FROM users WHERE username = ?", (username,)).rowcount
