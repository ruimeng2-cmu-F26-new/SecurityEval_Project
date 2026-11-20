# HAND-WRITTEN RULE-TEST FIXTURE for AST-LOG-001 (not a SecurityEval sample or LLM output).
def escaped(logger, username):
    cleaned = username.replace("\r", "\\r").replace("\n", "\\n")
    logger.info("Failed login for user: %s", cleaned)  # expect: AST-LOG-001


def repr_conversion(logger, username):
    logger.info(f"Failed login for user: {username!r}")  # expect: AST-LOG-001


def repr_placeholder(logger, username):
    logger.info("Failed login for user: %r", username)  # expect: AST-LOG-001
