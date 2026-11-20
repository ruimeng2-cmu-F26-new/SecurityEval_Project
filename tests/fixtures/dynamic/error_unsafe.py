"""Handwritten control, not LLM output. Vulnerable: returns the exception text."""
def run_computation(compute):
    try:
        return {"status": "ok", "result": compute()}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}
