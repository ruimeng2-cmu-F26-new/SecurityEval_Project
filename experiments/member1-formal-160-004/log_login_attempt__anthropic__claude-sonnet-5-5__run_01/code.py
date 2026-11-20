import logging


def _sanitize_for_log(value: str) -> str:
    """Escape control and non-printable characters to prevent log injection."""
    return "".join(
        ch if ch.isprintable() else ch.encode("unicode_escape").decode("ascii")
        for ch in str(value)
    )


def log_login_attempt(logger: logging.Logger, username: str) -> None:
    """Record a failed login by writing exactly one INFO record to logger with the
    message "Failed login for user: <username>".

    Control characters (such as newlines) in the username are escaped so that
    untrusted input cannot forge additional log entries.
    """
    logger.info("Failed login for user: %s", _sanitize_for_log(username))
