import html


def render_greeting(name: str) -> str:
    """Return an HTML fragment that greets the visitor: an h1 element whose text is
    "Hello, <name>!", where <name> is the visitor-supplied display name.
    """
    safe_name = html.escape(name, quote=True)
    return f"<h1>Hello, {safe_name}!</h1>"
