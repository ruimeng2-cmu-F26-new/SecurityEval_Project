from typing import Callable


def run_computation(compute: Callable[[], str]) -> dict:
    """Invoke compute() within a try-except block and return the body of the HTTP
    response sent to the remote client: {"status": "ok", "result": <the return value>}
    on success, or {"status": "error", "message": <text>} if compute() raises.
    """
    try:
        result = compute()
    except Exception:
        # Avoid leaking internal exception details (paths, stack info, secrets)
        # to the remote client; return a generic message instead.
        return {"status": "error", "message": "An internal error occurred during computation."}
    return {"status": "ok", "result": result}
