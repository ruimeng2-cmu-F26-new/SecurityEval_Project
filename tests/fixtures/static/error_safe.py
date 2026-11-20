# HAND-WRITTEN RULE-TEST FIXTURE for AST-ERR-001 (not a SecurityEval sample or LLM output).
import logging

log = logging.getLogger(__name__)


def generic(compute):
    try:
        return {"status": "ok", "result": compute()}
    except Exception:
        return {"status": "error", "message": "The computation failed."}


def logged_not_returned(compute):
    try:
        return compute()
    except Exception as exc:
        log.exception("computation failed: %s", exc)
        return None


def reraised(compute):
    try:
        return compute()
    except KeyError as exc:
        raise ValueError("bad input") from exc
