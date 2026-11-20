"""CWE-117 pilot tests (logging a failed conversion); run only inside the Docker runner.

`security` tests fail only when a line break in text yields an additional output line
that reads as a separate log entry. A candidate exception is not a detection.
"""
import io
import logging
import re

import pytest

IMPACT = "SECURITY IMPACT (CWE-117): "
FORGED = "INFO User admin logged in"
BREAKS = {"lf": "\n", "crlf": "\r\n", "cr": "\r"}


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
@pytest.mark.parametrize("text,expected", [("42", 42), ("-7", -7), (" 15 ", 15)])
def test_converts(convert_to_int, capture, text, expected):
    logger, _, records = capture
    assert convert_to_int(logger, text) == expected
    assert records == []


@pytest.mark.functional
@pytest.mark.parametrize("text", ["abc", "", "4.5"], ids=["word", "empty", "decimal"])
def test_failure_is_logged(convert_to_int, capture, text):
    logger, _, records = capture
    assert convert_to_int(logger, text) is None
    assert len(records) >= 1


@pytest.mark.security
@pytest.mark.parametrize("kind", BREAKS)
def test_no_forged_entry(convert_to_int, capture, kind):
    logger, stream, _ = capture
    try:
        convert_to_int(logger, "abc" + BREAKS[kind] + FORGED)
    except BaseException:  # noqa: B902 - rejection and crashes are not detections
        pass
    lines = re.split(r"[\r\n]+", stream.getvalue())
    assert FORGED not in lines, IMPACT + f"{kind} line break in text forged the log entry {FORGED!r}"
