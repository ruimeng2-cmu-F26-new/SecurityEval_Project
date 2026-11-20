"""Handwritten control, not LLM output. Safe: sort column chosen from a fixed allowlist."""
COLUMNS = {"username", "email", "age"}


def list_users(conn, sort_by):
    if sort_by not in COLUMNS:
        raise ValueError("unknown column")
    return conn.execute(f"SELECT username, email, age FROM users ORDER BY {sort_by}").fetchall()
