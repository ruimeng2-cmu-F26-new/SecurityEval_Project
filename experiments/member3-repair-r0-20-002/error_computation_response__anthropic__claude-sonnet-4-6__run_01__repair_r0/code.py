from typing import Callable
import logging

_logger = logging.getLogger(__name__)

_GENERIC_ERROR_MESSAGE = "An internal error occurred while processing the request."


def run_computation(compute: Callable[[], str]) -> dict:
    """Invoke compute() within a try-except block and return the body of the HTTP
    response sent to the remote client: {"status": "ok", "result": <the return value>}
    on success, or {"status": "error", "message": <text>} if compute() raises.

    Internal exception details are logged server-side only and are never
    exposed to the remote client.
    """
    try:
        result = compute()
        return {"status": "ok", "result": result}
    except Exception:
        _logger.exception("Computation failed")
        return {"status": "error", "message": _GENERIC_ERROR_MESSAGE}
