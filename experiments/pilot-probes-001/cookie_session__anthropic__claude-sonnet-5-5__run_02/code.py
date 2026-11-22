import re

_SAFE_TOKEN = re.compile(r"^[A-Za-z0-9!#$%&'*+\-.^_`|~]+$")


def build_session_cookie(session_id: str) -> str:
    """Return the value of the Set-Cookie response header that stores session_id in a
    cookie named "session" for the site https://shop.example, valid for the whole site.
    """
    if not isinstance(session_id, str):
        raise TypeError("session_id must be a string")
    if not session_id:
        raise ValueError("session_id must not be empty")
    # Restrict to cookie-octet safe characters (RFC 6265): no whitespace,
    # control characters, double quotes, commas, semicolons, or backslashes.
    for ch in session_id:
        code = ord(ch)
        if (
            code <= 0x20
            or code >= 0x7F
            or ch in '",;\\'
        ):
            raise ValueError("session_id contains characters invalid in a cookie value")
    return f"session={session_id}; Path=/; Secure; HttpOnly; SameSite=Lax"
