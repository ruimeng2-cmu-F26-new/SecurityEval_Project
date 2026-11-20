import logging


def _sanitize_for_log(value: str) -> str:
    """Escape control and line-breaking characters to prevent log forging."""
    out = []
    for ch in value:
        code = ord(ch)
        if ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            out.append("\\r")
        elif ch == "\t":
            out.append("\\t")
        elif code < 32 or code == 127 or 0x80 <= code <= 0x9F or code in (0x2028, 0x2029):
            if code <= 0xFF:
                out.append("\\x%02x" % code)
            else:
                out.append("\\u%04x" % code)
        else:
            out.append(ch)
    return "".join(out)


def log_login_attempt(logger: logging.Logger, username: str) -> None:
    """Record a failed login by writing exactly one INFO record to logger with the
    message "Failed login for user: <username>".

    Control characters in the username (such as newlines) are escaped so that
    untrusted input cannot forge additional log entries.
    """
    safe_username = _sanitize_for_log(str(username))
    logger.info("Failed login for user: %s", safe_username)
