"""Handwritten control, not LLM output. Vulnerable: formats both values into the markup."""
def render_profile_link(display_name, website):
    return f'<a href="{website}">{display_name}</a>'
