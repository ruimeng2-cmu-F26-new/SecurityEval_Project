# HAND-WRITTEN RULE-TEST FIXTURE for AST-LOG-001 (not a SecurityEval sample or LLM output).
import logging
import math


def constant_message(logger, username):
    if not username:
        logger.info("Failed login without a username")


def not_a_logger(value):
    return math.log(value)
