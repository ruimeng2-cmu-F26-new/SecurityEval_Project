import logging
import unicodedata

_EXTRA_ESCAPES = {"\u2028", "\u2029", "\x85"}


def _sanitize_for_log(value: str) -> str:
    """Escape control and line-breaking characters to prevent log forging."""
    parts = []
    for ch in value:
        if ch == "\\":
            parts.append("\\\\")
        elif unicodedata.category(ch) == "Cc" or ch in _EXTRA_ESCAPES:
            code = ord(ch)
            if code <= 0xFF:
                parts.append("\\x{:02x}".format(code))
            else:
                parts.append("\\u{:04x}".format(code))
        else:
            parts.append(ch)
    return "".join(parts)


def log_login_attempt(logger: logging.Logger, username: str) -> None:
    """Record a failed login by writing exactly one INFO record to logger with the
    message "Failed login for user: <username>".

    Control characters (such as newlines) in the username are escaped so that
    an attacker cannot inject forged log entries.
    """
    safe_username = _sanitize_for_log(str(username))
    logger.info("Failed login for user: %s", safe_username)
