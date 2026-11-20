import ssl


def get_ssl_context() -> ssl.SSLContext:
    """Create an SSL context for a client that connects to HTTPS servers and return it."""
    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED
    try:
        context.set_alpn_protocols(["h2", "http/1.1"])
    except (NotImplementedError, ssl.SSLError):
        pass
    return context
