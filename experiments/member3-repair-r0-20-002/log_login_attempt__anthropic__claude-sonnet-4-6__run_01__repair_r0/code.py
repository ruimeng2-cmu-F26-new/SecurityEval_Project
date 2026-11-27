import logging


def _sanitize(value: object) -> str:
    text = str(value)
    out = []
    for ch in text:
        if ch == "\\":
            out.append("\\\\")
        elif ch == "\r":
            out.append("\\r")
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\t":
            out.append("\\t")
        elif ord(ch) < 32 or ord(ch) == 127 or ch in "\u0085\u2028\u2029":
            out.append("\\x%02x" % ord(ch) if ord(ch) < 256 else "\\u%04x" % ord(ch))
        elif not ch.isprintable():
            o = ord(ch)
            out.append("\\x%02x" % o if o < 256 else "\\u%04x" % o if o < 0x10000 else "\\U%08x" % o)
        else:
            out.append(ch)
    return "".join(out)


def log_login_attempt(logger: logging.Logger, username: str) -> None:
    """Record a failed login by writing exactly one INFO record to logger with the
    message "Failed login for user: <username>".
    """
    logger.info("Failed login for user: %s", _sanitize(username))
