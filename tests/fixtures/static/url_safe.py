# HAND-WRITTEN RULE-TEST FIXTURE for AST-URL-001 (not a SecurityEval sample or LLM output).
from urllib.parse import urlsplit


def parsed_host(url):
    parts = urlsplit(url)
    host = parts.hostname or ""
    return parts.scheme in ("http", "https") and (host == "example.com" or host.endswith(".example.com"))


def scheme_only(url):
    return url.startswith(("http://", "https://"))


def file_extension(name):
    return name.endswith(".log") or "error" in name
