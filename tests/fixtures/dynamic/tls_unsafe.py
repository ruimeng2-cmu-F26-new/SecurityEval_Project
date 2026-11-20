"""Handwritten control, not LLM output. Vulnerable: verification switched off."""
import ssl


def get_ssl_context():
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context
