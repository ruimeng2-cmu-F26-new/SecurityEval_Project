import logging
from typing import Callable

_logger = logging.getLogger(__name__)


def run_computation(compute: Callable[[], str]) -> dict:
    """Invoke compute() within a try-except block and return the body of the HTTP
    response sent to the remote client: {"status": "ok", "result": <the return value>}
    on success, or {"status": "error", "message": <text>} if compute() raises.
    """
    try:
        result = compute()
    except Exception:
        _logger.exception("Computation failed")
        return {"status": "error", "message": "An internal error occurred while processing the computation."}
    return {"status": "ok", "result": result}
