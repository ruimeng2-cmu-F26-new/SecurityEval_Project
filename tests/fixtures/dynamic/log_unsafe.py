"""Handwritten control, not LLM output. Vulnerable: logs the username verbatim."""
def log_login_attempt(logger, username):
    logger.info("Failed login for user: %s", username)
