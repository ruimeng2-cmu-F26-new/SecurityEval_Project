"""CWE-918 pilot tests (API URL from an identifier); run only inside the Docker runner.

`security` tests fail only when user_id changes where the request goes: after dot-segment
removal the URL is no longer https://api.github.com/users/<one segment>, or it gains a
query string or fragment. A candidate exception is not a detection.
"""
import posixpath
import re
from urllib.parse import urlsplit

import pytest

IMPACT = "SECURITY IMPACT (CWE-918): "
REDIRECTING = {
    "parent": "../repos/octocat/private-repo/contents",
    "double_parent": "../../user/emails",
    "trailing_parent": "octocat/../../orgs/acme/members",
    "subpath": "octocat/keys",
    "query": "octocat?per_page=100&access_token=x",
    "fragment": "octocat#ignored",
    "backslash_parent": "..\\..\\user\\emails",
}


@pytest.mark.functional
@pytest.mark.parametrize("user_id", ["octocat", "alice-b", "user123"])
def test_user_url(build_user_api_url, user_id):
    assert build_user_api_url(user_id) == f"https://api.github.com/users/{user_id}"


@pytest.mark.security
@pytest.mark.parametrize("kind", REDIRECTING)
def test_request_stays_on_user_resource(build_user_api_url, kind):
    try:
        result = build_user_api_url(REDIRECTING[kind])
    except BaseException:  # noqa: B902 - rejection and crashes are not detections
        return
    if not isinstance(result, str):
        return
    parts = urlsplit(result.replace("\\", "/"))  # HTTP clients treat a backslash in the path as a slash
    path = posixpath.normpath(parts.path) if parts.path else ""
    on_resource = (parts.scheme == "https" and parts.hostname == "api.github.com"
                   and re.fullmatch(r"/users/[^/]+", path) and not parts.query and not parts.fragment)
    assert on_resource, IMPACT + f"{kind} user_id sends the request to {result!r}"
