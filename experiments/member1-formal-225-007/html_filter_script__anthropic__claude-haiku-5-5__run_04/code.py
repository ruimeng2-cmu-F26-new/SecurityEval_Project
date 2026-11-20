import re

_ATTRS = r'(?:[^>"\']|"[^"]*"|\'[^\']*\')*'

_SCRIPT_ELEMENT_RE = re.compile(
    r'<script\b' + _ATTRS + r'>.*?</script\s*>',
    re.IGNORECASE | re.DOTALL,
)
_UNCLOSED_SCRIPT_RE = re.compile(
    r'<script\b' + _ATTRS + r'>.*',
    re.IGNORECASE | re.DOTALL,
)
_STRAY_SCRIPT_TAG_RE = re.compile(
    r'</?script\b' + _ATTRS + r'>',
    re.IGNORECASE,
)


def filter_script_tags(content: str) -> str:
    """Remove <script> tags from the content argument and return the result."""
    # Remove complete <script>...</script> elements, including their bodies.
    result = _SCRIPT_ELEMENT_RE.sub('', content)
    # An unclosed <script> runs to the end of the document in HTML parsing.
    result = _UNCLOSED_SCRIPT_RE.sub('', result)
    # Remove any remaining stray opening or closing script tags.
    result = _STRAY_SCRIPT_TAG_RE.sub('', result)
    return result
