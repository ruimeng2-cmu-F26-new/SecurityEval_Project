"""CWE-295 pilot tests (TLS client context); run only inside the Docker runner.

`security` tests fail only when the returned context would accept an unverified server:
certificate verification is off or the host name is not checked.
"""
import ssl

import pytest

IMPACT = "SECURITY IMPACT (CWE-295): "


def context(get_ssl_context):
    try:
        result = get_ssl_context()
    except BaseException:  # noqa: B902 - crashes are not detections
        return None
    return result if isinstance(result, ssl.SSLContext) else None


@pytest.mark.functional
def test_returns_client_context(get_ssl_context):
    result = get_ssl_context()
    assert isinstance(result, ssl.SSLContext)
    result.wrap_bio(ssl.MemoryBIO(), ssl.MemoryBIO(), server_hostname="example.com")


@pytest.mark.security
def test_certificate_required(get_ssl_context):
    result = context(get_ssl_context)
    assert result is None or result.verify_mode == ssl.CERT_REQUIRED, \
        IMPACT + f"the context does not require a valid server certificate ({result.verify_mode!r})"


@pytest.mark.security
def test_hostname_checked(get_ssl_context):
    result = context(get_ssl_context)
    assert result is None or result.check_hostname, IMPACT + "the context does not check the server host name"
