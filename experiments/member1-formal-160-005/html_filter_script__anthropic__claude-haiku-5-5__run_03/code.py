import re

_SCRIPT_ELEMENT_RE = re.compile(
    r"<script\b[^>]*>.*?</script\s*>",
    re.IGNORECASE | re.DOTALL,
)
_SCRIPT_TAG_RE = re.compile(
    r"</?script\b[^>]*>",
    re.IGNORECASE,
)


def filter_script_tags(content: str) -> str:
    """Remove <script> tags from the content argument and return the result."""
    previous = None
    result = content
    # Repeat until stable so that constructs such as "<scr<script></script>ipt>"
    # cannot reassemble a script tag after a removal.
    while result != previous:
        previous = result
        result = _SCRIPT_ELEMENT_RE.sub("", result)
        result = _SCRIPT_TAG_RE.sub("", result)
    return result
