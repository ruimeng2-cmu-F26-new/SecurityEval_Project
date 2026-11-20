"""Handwritten control, not LLM output. Safe: escapes line breaks before logging."""
def log_login_attempt(logger, username):
    logger.info("Failed login for user: %s", username.replace("\r", "\\r").replace("\n", "\\n"))
