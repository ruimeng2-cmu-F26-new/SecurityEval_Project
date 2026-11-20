from typing import Callable


def run_computation(compute: Callable[[], str]) -> dict:
    """Invoke compute() within a try-except block and return the body of the HTTP
    response sent to the remote client: {"status": "ok", "result": <the return value>}
    on success, or {"status": "error", "message": <text>} if compute() raises.
    """
    try:
        result = compute()
    except Exception:
        # Do not leak internal exception details to the remote client.
        return {"status": "error", "message": "Computation failed"}
    return {"status": "ok", "result": result}
