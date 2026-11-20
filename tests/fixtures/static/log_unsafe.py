# HAND-WRITTEN RULE-TEST FIXTURE for AST-LOG-001 (not a SecurityEval sample or LLM output).
import logging

log = logging.getLogger(__name__)


def percent_style(logger, username):
    logger.info("Failed login for user: %s", username)  # expect: AST-LOG-001


def formatted(logger, username):
    logger.info(f"Failed login for user: {username}")  # expect: AST-LOG-001


def concatenated(username):
    message = "Failed login for user: " + username
    log.warning(message)  # expect: AST-LOG-001


def module_level(username):
    logging.error("Failed login for user: %s" % username)  # expect: AST-LOG-001


def with_level(logger, username):
    logger.log(logging.INFO, "Failed login for user: %s", username.strip())  # expect: AST-LOG-001
