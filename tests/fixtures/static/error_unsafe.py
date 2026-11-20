# HAND-WRITTEN RULE-TEST FIXTURE for AST-ERR-001 (not a SecurityEval sample or LLM output).
import traceback


def exception_text(compute):
    try:
        return {"status": "ok", "result": compute()}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}  # expect: AST-ERR-001


def formatted(compute):
    try:
        return compute()
    except ValueError as error:
        return f"failed: {error}"  # expect: AST-ERR-001


def stack_trace(compute):
    try:
        return compute()
    except Exception:
        return {"status": "error", "message": traceback.format_exc()}  # expect: AST-ERR-001


def carried_out(compute):
    message = None
    try:
        result = compute()
    except Exception as exc:
        message = "error: " + repr(exc)
    if message:
        return {"status": "error", "message": message}  # expect: AST-ERR-001
    return {"status": "ok", "result": result}


def class_name(compute):
    try:
        return compute()
    except Exception as exc:
        return {"status": "error", "message": type(exc).__name__}  # expect: AST-ERR-001
