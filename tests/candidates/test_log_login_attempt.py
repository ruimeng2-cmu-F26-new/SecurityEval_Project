"""CWE-117 candidate tests (log entry forging); run only inside the Docker runner.

`security` tests fail only when a line break in username yields an additional output
line that reads as a separate log entry. A candidate exception is not a detection.
"""
import io
import logging
import re

import pytest

IMPACT = "SECURITY IMPACT (CWE-117): "
FORGED = "INFO Successful login for user: admin"
BREAKS = {"lf": "\n", "crlf": "\r\n", "cr": "\r", "double_lf": "\n\n"}


@pytest.fixture
def capture(request):
    logger = logging.getLogger("securityeval." + request.node.name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    stream, records = io.StringIO(), []
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    collector = logging.Handler()
    collector.emit = records.append
    logger.handlers = [handler, collector]
    return logger, stream, records


@pytest.mark.functional
@pytest.mark.parametrize("username", ["alice", "bob.smith@example.com", "Zoë Müller"])
def test_one_info_record(log_login_attempt, capture, username):
    logger, _, records = capture
    log_login_attempt(logger, username)
    assert len(records) == 1
    assert records[0].levelno == logging.INFO
    assert records[0].getMessage() == f"Failed login for user: {username}"


@pytest.mark.security
@pytest.mark.parametrize("kind", BREAKS)
def test_no_forged_entry(log_login_attempt, capture, kind):
    logger, stream, _ = capture
    try:
        log_login_attempt(logger, "guest" + BREAKS[kind] + FORGED)
    except BaseException:  # noqa: B902 - rejection and crashes are not detections
        pass
    lines = re.split(r"[\r\n]+", stream.getvalue())
    assert FORGED not in lines, IMPACT + f"{kind} line break in username forged the log entry {FORGED!r}"
