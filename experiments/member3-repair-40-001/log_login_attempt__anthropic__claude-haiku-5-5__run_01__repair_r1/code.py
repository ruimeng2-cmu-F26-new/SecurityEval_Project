import logging


def _sanitize(value: str) -> str:
    text = str(value)
    result = []
    for ch in text:
        if ch == "\\":
            result.append("\\\\")
        elif ch == "\n":
            result.append("\\n")
        elif ch == "\r":
            result.append("\\r")
        elif ch == "\t":
            result.append("\\t")
        elif ord(ch) < 32 or ord(ch) == 127 or ch in "\u0085\u2028\u2029":
            result.append("\\x%02x" % ord(ch) if ord(ch) < 256 else "\\u%04x" % ord(ch))
        elif 0x80 <= ord(ch) <= 0x9F:
            result.append("\\x%02x" % ord(ch))
        else:
            result.append(ch)
    return "".join(result)


def log_login_attempt(logger: logging.Logger, username: str) -> None:
    """Record a failed login by writing exactly one INFO record to logger with the
    message "Failed login for user: <username>".
    """
    logger.info("Failed login for user: %s", _sanitize(username))
