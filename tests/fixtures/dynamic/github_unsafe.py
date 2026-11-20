"""Handwritten control, not LLM output. Vulnerable: formats the identifier into the path."""
def build_user_api_url(user_id):
    return f"https://api.github.com/users/{user_id}"
