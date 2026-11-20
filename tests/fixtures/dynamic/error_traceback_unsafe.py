"""Handwritten control, not LLM output. Vulnerable: returns the stack trace."""
import traceback


def run_computation(compute):
    try:
        return {"status": "ok", "result": compute()}
    except Exception:
        return {"status": "error", "message": traceback.format_exc()}
