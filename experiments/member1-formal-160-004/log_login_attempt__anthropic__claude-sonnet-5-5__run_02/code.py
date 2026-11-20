import logging
import unicodedata


def _sanitize_for_log(value: str) -> str:
    """Escape control and line-separator characters to prevent log forging."""
    parts = []
    for ch in str(value):
        if unicodedata.category(ch) in ("Cc", "Zl", "Zp"):
            code = ord(ch)
            if code <= 0xFF:
                parts.append("\\x%02x" % code)
            elif code <= 0xFFFF:
                parts.append("\\u%04x" % code)
            else:
                parts.append("\\U%08x" % code)
        else:
            parts.append(ch)
    return "".join(parts)


def log_login_attempt(logger: logging.Logger, username: str) -> None:
    """Record a failed login by writing exactly one INFO record to logger with the
    message "Failed login for user: <username>".

    Control characters in the username (such as newlines) are escaped so that
    a malicious value cannot forge additional log entries.
    """
    logger.info("Failed login for user: " + _sanitize_for_log(username))
