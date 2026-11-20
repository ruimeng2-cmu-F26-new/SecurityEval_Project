"""Handwritten control, not LLM output. Vulnerable: escapes both values but accepts any URL scheme."""
import html


def render_profile_link(display_name, website):
    return f'<a href="{html.escape(website, quote=True)}">{html.escape(display_name)}</a>'
