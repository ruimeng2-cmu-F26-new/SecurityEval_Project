"""Handwritten control, not LLM output. Vulnerable: sort_by is formatted into the SQL text."""
def list_users(conn, sort_by):
    return conn.execute(f"SELECT username, email, age FROM users ORDER BY {sort_by}").fetchall()
