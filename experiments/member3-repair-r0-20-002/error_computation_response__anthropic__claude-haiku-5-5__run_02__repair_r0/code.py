from typing import Callable
import logging

_logger = logging.getLogger(__name__)


def run_computation(compute: Callable[[], str]) -> dict:
    """Invoke compute() within a try-except block and return the body of the HTTP
    response sent to the remote client: {"status": "ok", "result": <the return value>}
    on success, or {"status": "error", "message": <text>} if compute() raises.
    """
    try:
        result = compute()
    except Exception:
        # Log details server-side only; never expose internal error text to the client.
        _logger.exception("Computation failed")
        return {"status": "error", "message": "An internal error occurred."}
    return {"status": "ok", "result": result}
