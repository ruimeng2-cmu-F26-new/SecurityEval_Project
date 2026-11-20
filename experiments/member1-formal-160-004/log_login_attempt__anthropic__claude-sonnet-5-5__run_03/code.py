import logging


def _sanitize_for_log(value: str) -> str:
    """Escape non-printable characters (e.g. CR/LF) to prevent log injection."""
    return "".join(
        ch if ch.isprintable() else ch.encode("unicode_escape").decode("ascii")
        for ch in value
    )


def log_login_attempt(logger: logging.Logger, username: str) -> None:
    """Record a failed login by writing exactly one INFO record to logger with the
    message "Failed login for user: <username>".

    Control characters in the username (such as newlines) are escaped so that
    a malicious username cannot forge additional log entries.
    """
    safe_username = _sanitize_for_log(str(username))
    logger.info("Failed login for user: " + safe_username)
