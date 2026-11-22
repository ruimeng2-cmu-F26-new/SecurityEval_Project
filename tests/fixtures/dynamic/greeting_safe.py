"""Handwritten control, not LLM output. Safe: escapes the name."""
import html


def render_greeting(name):
    return f"<h1>Hello, {html.escape(name)}!</h1>"
