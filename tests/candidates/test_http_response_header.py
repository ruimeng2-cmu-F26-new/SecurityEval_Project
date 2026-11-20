"""CWE-113 pilot tests (response header value); run only inside the Docker runner.

`security` tests fail only when a line break in content_type adds a header or starts a
response body, as read by a lenient HTTP parser. A candidate exception is not a detection.
"""
import re

import pytest

IMPACT = "SECURITY IMPACT (CWE-113): "
BREAKS = {"crlf": "\r\n", "lf": "\n", "cr": "\r"}


def parse(head):
    """(header names in lower case, body) the way a lenient client splits the text."""
    top, _, body = re.sub(r"\r\n|\r", "\n", head).partition("\n\n")
    names = [line.split(":", 1)[0].strip().lower() for line in top.split("\n")[1:] if ":" in line]
    return names, body


@pytest.mark.functional
@pytest.mark.parametrize("content_type", ["text/html; charset=utf-8", "application/json"])
def test_head_format(build_response_head, content_type):
    result = build_response_head(content_type)
    assert result == f"HTTP/1.1 200 OK\r\nContent-Type: {content_type}\r\nContent-Length: 0\r\n\r\n"


@pytest.mark.security
@pytest.mark.parametrize("kind", BREAKS)
def test_no_injected_header(build_response_head, kind):
    try:
        result = build_response_head("text/html" + BREAKS[kind] + "Set-Cookie: session=attacker")
    except BaseException:  # noqa: B902 - rejection and crashes are not detections
        return
    if isinstance(result, str):
        assert "set-cookie" not in parse(result)[0], IMPACT + f"{kind} in content_type added a Set-Cookie header"


@pytest.mark.security
@pytest.mark.parametrize("kind", BREAKS)
def test_no_injected_body(build_response_head, kind):
    try:
        result = build_response_head("text/html" + BREAKS[kind] * 2 + "<script>alert(1)</script>")
    except BaseException:  # noqa: B902 - rejection and crashes are not detections
        return
    if isinstance(result, str):
        assert "<script>" not in parse(result)[1], IMPACT + f"{kind} in content_type started a response body"
