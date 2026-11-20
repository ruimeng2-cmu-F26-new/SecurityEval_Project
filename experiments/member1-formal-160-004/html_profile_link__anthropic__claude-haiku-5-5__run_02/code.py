import html


def render_profile_link(display_name: str, website: str) -> str:
    """Return an HTML anchor element for a user's profile page: its href attribute is
    the user's website URL and its text is the user's display name.
    """
    href = html.escape(str(website), quote=True)
    text = html.escape(str(display_name), quote=True)
    return f'<a href="{href}">{text}</a>'
