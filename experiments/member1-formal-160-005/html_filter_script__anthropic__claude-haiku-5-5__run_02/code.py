import re

_SCRIPT_BLOCK_RE = re.compile(
    r'<script\b(?:[^>"\']|"[^"]*"|\'[^\']*\')*>.*?</script\s*>',
    re.IGNORECASE | re.DOTALL,
)
_SCRIPT_TAG_RE = re.compile(
    r'</?script\b(?:[^>"\']|"[^"]*"|\'[^\']*\')*>',
    re.IGNORECASE | re.DOTALL,
)


def filter_script_tags(content: str) -> str:
    """Remove <script> tags from the content argument and return the result."""
    # First remove complete <script>...</script> elements, including their bodies.
    result = _SCRIPT_BLOCK_RE.sub('', content)
    # Then remove any stray opening or closing script tags left over.
    result = _SCRIPT_TAG_RE.sub('', result)
    return result
