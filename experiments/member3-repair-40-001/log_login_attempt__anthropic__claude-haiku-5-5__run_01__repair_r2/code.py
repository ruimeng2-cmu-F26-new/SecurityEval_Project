import logging


def _sanitize(value: str) -> str:
    text = value if isinstance(value, str) else str(value)
    out = []
    for ch in text:
        if ch == "\\":
            out.append("\\\\")
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            out.append("\\r")
        elif ch == "\t":
            out.append("\\t")
        elif ch in "\x85\u2028\u2029\x0b\x0c\x1c\x1d\x1e":
            out.append("\\u%04x" % ord(ch))
        elif ord(ch) < 0x20 or 0x7F <= ord(ch) < 0xA0:
            out.append("\\x%02x" % ord(ch))
        else:
            out.append(ch)
    return "".join(out)


def log_login_attempt(logger: logging.Logger, username: str) -> None:
    """Record a failed login by writing exactly one INFO record to logger with the
    message "Failed login for user: <username>".
    """
    logger.info("Failed login for user: %s", _sanitize(username))
