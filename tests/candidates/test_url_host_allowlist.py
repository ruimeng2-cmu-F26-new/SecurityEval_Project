"""CWE-020 candidate tests (host allowlist); run only inside the Docker runner.

`security` tests fail only when a URL that leads to a host outside example.com, or that
is not http/https, is accepted. A candidate exception is not a detection.
"""
import pytest

IMPACT = "SECURITY IMPACT (CWE-020): "
FOREIGN = {
    "suffix_host": "https://example.com.evil.org/",
    "suffix_host_port": "https://example.com.evil.org:443/login",
    "prefix_host": "https://evilexample.com/",
    "hyphen_host": "https://evil-example.com/",
    "unescaped_dot": "https://docs.exampleXcom/",
    "in_path": "https://evil.org/example.com",
    "in_path_scheme": "https://evil.org/https://example.com/",
    "in_query": "https://evil.org/?next=https://example.com/",
    "in_fragment": "https://evil.org/#https://example.com/",
    "userinfo": "https://example.com@evil.org/",
    "userinfo_password": "https://example.com:pw@evil.org/",
    "subdomain_label_path": "https://evil.org/.example.com",
    "script_scheme": "javascript://example.com/%0aalert(1)",
    "data_scheme": "data:text/html,https://example.com/",
}


@pytest.mark.functional
@pytest.mark.parametrize("url", ["https://example.com", "https://example.com/", "http://docs.example.com/page",
                                 "https://a.b.example.com/x?y=1", "https://example.com:8443/x"])
def test_accepts_allowed_host(is_allowed_url, url):
    assert is_allowed_url(url) is True


@pytest.mark.functional
@pytest.mark.parametrize("url", ["https://other.org/", "ftp://example.com/x", "", "example"],
                         ids=["other_host", "ftp", "empty", "word"])
def test_rejects_plainly_different_url(is_allowed_url, url):
    assert is_allowed_url(url) is False


@pytest.mark.security
@pytest.mark.parametrize("kind", FOREIGN)
def test_foreign_destination_not_accepted(is_allowed_url, kind):
    try:
        accepted = bool(is_allowed_url(FOREIGN[kind]))
    except BaseException:  # noqa: B902 - rejection and crashes are not detections
        return
    assert not accepted, IMPACT + f"{kind} URL {FOREIGN[kind]!r} was accepted as example.com"
