# HAND-WRITTEN RULE-TEST FIXTURE for AST-URL-001 (not a SecurityEval sample or LLM output).
import re
from urllib.parse import urlparse


def substring(url):
    return "example.com" in url  # expect: AST-URL-001


def substring_of_host(url):
    host = urlparse(url).hostname or ""
    return "example.com" in host  # expect: AST-URL-001


def suffix_without_dot(url):
    host = urlparse(url).hostname or ""
    return host == "example.com" or host.endswith("example.com")  # expect: AST-URL-001


def open_prefix(url):
    return url.startswith(("https://example.com", "http://example.com"))  # expect: AST-URL-001


def unescaped_dot(url):
    return re.fullmatch(r"https?://([a-z0-9-]+\.)*example.com(/.*)?", url) is not None  # expect: AST-URL-001


def no_end_anchor(url):
    return bool(re.match(r"^https?://([a-z0-9-]+\.)*example\.com", url))  # expect: AST-URL-001
