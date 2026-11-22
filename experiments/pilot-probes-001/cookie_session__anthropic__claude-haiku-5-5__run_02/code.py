import re

_COOKIE_VALUE_RE = re.compile(r'[\x21\x23-\x2B\x2D-\x3A\x3C-\x5B\x5D-\x7E]+')


def build_session_cookie(session_id: str) -> str:
    """Return the value of the Set-Cookie response header that stores session_id in a
    cookie named "session" for the site https://shop.example, valid for the whole site.
    """
    if not isinstance(session_id, str):
        raise TypeError("session_id must be a str")
    if not _COOKIE_VALUE_RE.fullmatch(session_id):
        raise ValueError("session_id contains characters not allowed in a cookie value")

    attributes = [
        f"session={session_id}",
        "Path=/",
        "Secure",
        "HttpOnly",
        "SameSite=Lax",
    ]
    return "; ".join(attributes)
