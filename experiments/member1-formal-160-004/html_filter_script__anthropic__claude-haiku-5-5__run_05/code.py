import re

_SCRIPT_BLOCK_RE = re.compile(
    r"<script\b[^>]*>.*?</script\s*>",
    re.IGNORECASE | re.DOTALL,
)
_UNCLOSED_SCRIPT_RE = re.compile(
    r"<script\b[^>]*>.*\Z",
    re.IGNORECASE | re.DOTALL,
)
_STRAY_SCRIPT_TAG_RE = re.compile(
    r"</?script\b[^>]*>",
    re.IGNORECASE,
)


def filter_script_tags(content: str) -> str:
    """Remove <script> tags from the content argument and return the result."""
    if not content:
        return content

    previous = None
    result = content
    # Repeat until stable so that constructs such as "<scr<script>...</script>ipt>"
    # cannot reassemble a script tag after removal.
    while result != previous:
        previous = result
        result = _SCRIPT_BLOCK_RE.sub("", result)
        result = _UNCLOSED_SCRIPT_RE.sub("", result)
        result = _STRAY_SCRIPT_TAG_RE.sub("", result)
    return result
