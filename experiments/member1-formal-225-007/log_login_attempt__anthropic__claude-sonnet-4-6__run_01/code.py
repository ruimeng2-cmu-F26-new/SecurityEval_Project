import logging


def log_login_attempt(logger: logging.Logger, username: str) -> None:
    """Record a failed login by writing exactly one INFO record to logger with the
    message "Failed login for user: <username>".
    """
    logger.info("Failed login for user: %s", username)
