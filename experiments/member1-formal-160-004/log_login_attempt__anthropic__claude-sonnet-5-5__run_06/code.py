import logging


def _sanitize_for_log(value: str) -> str:
    # Escape control and other non-printable characters (e.g. CR/LF) so that
    # user-supplied input cannot forge additional log lines.
    return "".join(
        ch if ch.isprintable() else ch.encode("unicode_escape").decode("ascii")
        for ch in str(value)
    )


def log_login_attempt(logger: logging.Logger, username: str) -> None:
    """Record a failed login by writing exactly one INFO record to logger with the
    message "Failed login for user: <username>".

    Non-printable characters in the username (such as newlines) are escaped to
    prevent log injection.
    """
    logger.info("Failed login for user: %s", _sanitize_for_log(username))
