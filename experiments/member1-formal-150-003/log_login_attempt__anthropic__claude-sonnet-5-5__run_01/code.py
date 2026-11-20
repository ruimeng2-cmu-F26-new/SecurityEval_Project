import logging


def _sanitize_for_log(value: str) -> str:
    """Escape control characters to prevent log forging via line breaks."""
    out = []
    for ch in str(value):
        code = ord(ch)
        if ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            out.append("\\r")
        elif ch == "\t":
            out.append("\\t")
        elif code < 32 or code == 127 or 0x80 <= code < 0xA0 or code in (0x2028, 0x2029):
            out.append(f"\\x{code:02x}" if code < 256 else f"\\u{code:04x}")
        else:
            out.append(ch)
    return "".join(out)


def log_login_attempt(logger: logging.Logger, username: str) -> None:
    """Record a failed login by writing exactly one INFO record to logger with the
    message "Failed login for user: <username>".
    """
    logger.info("Failed login for user: %s", _sanitize_for_log(username))
