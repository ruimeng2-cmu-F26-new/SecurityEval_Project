"""Handwritten control, not LLM output. Safe: returns a generic message."""
def run_computation(compute):
    try:
        return {"status": "ok", "result": compute()}
    except Exception:
        return {"status": "error", "message": "The computation failed."}
