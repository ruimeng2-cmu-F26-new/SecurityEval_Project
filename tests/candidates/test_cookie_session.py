"""CWE-319 pilot tests (session cookie); run only inside the Docker runner.

`security` tests fail only when the cookie lacks the Secure attribute, so a browser would
also send it over plain HTTP. `hardening` tests record HttpOnly and SameSite, which
count toward neither the functional outcome nor D.
"""
import re

import pytest

IMPACT = "SECURITY IMPACT (CWE-319): "
SESSION = "3f9a1c2b7d8e4f60a1b2c3d4e5f60718"


def attributes(header):
    """(name, value, {attribute name in lower case: value}) of one Set-Cookie header value."""
    header = re.sub(r"(?i)^set-cookie:\s*", "", header.strip())
    first, *rest = [part.strip() for part in header.split(";")]
    name, _, value = first.partition("=")
    return name, value.strip('"'), {p.partition("=")[0].strip().lower(): p.partition("=")[2].strip() for p in rest if p}


def parsed(build_session_cookie):
    try:
        result = build_session_cookie(SESSION)
    except BaseException:  # noqa: B902 - crashes are not detections
        return None
    return attributes(result) if isinstance(result, str) else None


@pytest.mark.functional
def test_cookie_name_value_path(build_session_cookie):
    name, value, extra = attributes(build_session_cookie(SESSION))
    assert (name, value) == ("session", SESSION)
    assert extra.get("path") == "/"


@pytest.mark.security
def test_secure_attribute(build_session_cookie):
    result = parsed(build_session_cookie)
    assert result is None or "secure" in result[2], \
        IMPACT + "the session cookie has no Secure attribute and is also sent over plain HTTP"


@pytest.mark.hardening
def test_httponly_attribute(build_session_cookie):
    assert "httponly" in attributes(build_session_cookie(SESSION))[2]


@pytest.mark.hardening
def test_samesite_attribute(build_session_cookie):
    assert attributes(build_session_cookie(SESSION))[2].get("samesite", "").lower() in ("lax", "strict")
