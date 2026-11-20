import re

_SCRIPT_OPEN = r"<script\b(?:[^>\"']|\"[^\"]*\"|'[^']*')*>"
_SCRIPT_CLOSE = r"</script\s*>"

_SCRIPT_BLOCK_RE = re.compile(
    _SCRIPT_OPEN + r".*?" + _SCRIPT_CLOSE,
    re.IGNORECASE | re.DOTALL,
)
_SCRIPT_TAG_RE = re.compile(
    r"(?:" + _SCRIPT_OPEN + r"|" + _SCRIPT_CLOSE + r")",
    re.IGNORECASE | re.DOTALL,
)


def filter_script_tags(content: str) -> str:
    """Remove <script> tags from the content argument and return the result."""
    previous = None
    result = content
    # Repeat until stable so that removals cannot reassemble new script tags.
    while result != previous:
        previous = result
        result = _SCRIPT_BLOCK_RE.sub("", result)
        result = _SCRIPT_TAG_RE.sub("", result)
    return result
