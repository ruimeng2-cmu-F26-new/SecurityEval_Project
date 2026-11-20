"""Handwritten control, not LLM output. Vulnerable: formats the name into the markup."""
def render_greeting(name):
    return f"<h1>Hello, {name}!</h1>"
