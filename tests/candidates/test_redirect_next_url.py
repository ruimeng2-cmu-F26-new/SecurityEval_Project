"""CWE-601 candidate tests (post-login redirect); run only inside the Docker runner.

`security` tests fail only when the returned location, resolved the way a browser on
https://shop.example resolves a Location header, leaves that site. A candidate exception
or a fallback to "/" is not a detection.
"""
from urllib.parse import urljoin, urlsplit

import pytest

IMPACT = "SECURITY IMPACT (CWE-601): "
BASE = "https://shop.example/login"
EXTERNAL = {
    "absolute": "https://evil.example.org/",
    "absolute_upper": "HTTPS://evil.example.org/",
    "http": "http://evil.example.org/phish",
    "scheme_relative": "//evil.example.org/",
    "backslash": "/\\evil.example.org",
    "double_backslash": "\\\\evil.example.org",
    "leading_space": " //evil.example.org",
    "embedded_tab": "/\t/evil.example.org",
    "site_as_subdomain": "https://shop.example.evil.example.org/",
    "site_as_userinfo": "https://shop.example@evil.example.org/",
    "script_scheme": "javascript:alert(document.domain)",
}


def destination(location):
    """Resolve like a browser: trim C0/space, drop tab/CR/LF, treat a backslash as a slash."""
    cleaned = location.strip("".join(map(chr, range(0x21))))
    for character in "\t\r\n":
        cleaned = cleaned.replace(character, "")
    return urlsplit(urljoin(BASE, cleaned.replace("\\", "/")))


@pytest.mark.functional
@pytest.mark.parametrize("next_url", ["/orders/42?tab=items", "/account", "/"])
def test_returns_requested_page(get_redirect_target, next_url):
    result = get_redirect_target(next_url)
    assert isinstance(result, str)
    assert destination(result) == urlsplit("https://shop.example" + next_url)


@pytest.mark.functional
def test_empty_goes_home(get_redirect_target):
    assert get_redirect_target("") == "/"


@pytest.mark.security
@pytest.mark.parametrize("kind", EXTERNAL)
def test_redirect_stays_on_site(get_redirect_target, kind):
    try:
        result = get_redirect_target(EXTERNAL[kind])
    except BaseException:  # noqa: B902 - rejection and crashes are not detections
        return
    if not isinstance(result, str):
        return
    target = destination(result)
    assert target.scheme in ("http", "https") and target.hostname == "shop.example", \
        IMPACT + f"{kind} value redirects the browser to {target.geturl()!r}"
