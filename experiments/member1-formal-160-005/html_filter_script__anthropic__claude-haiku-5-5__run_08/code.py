import re

_SCRIPT_OPEN_ATTRS = r'(?:[^>"\']|"[^"]*"|\'[^\']*\')*'
_SCRIPT_BLOCK_RE = re.compile(
    r'<script\b' + _SCRIPT_OPEN_ATTRS + r'>.*?</script\s*>',
    re.IGNORECASE | re.DOTALL,
)
_SCRIPT_TAG_RE = re.compile(
    r'</?script\b' + _SCRIPT_OPEN_ATTRS + r'/?>',
    re.IGNORECASE | re.DOTALL,
)


def filter_script_tags(content: str) -> str:
    """Remove <script> tags from the content argument and return the result."""
    previous = None
    result = content
    # Repeat until stable so that nested constructs such as
    # "<scr<script>x</script>ipt>" cannot reassemble a script tag.
    while result != previous:
        previous = result
        result = _SCRIPT_BLOCK_RE.sub('', result)
        result = _SCRIPT_TAG_RE.sub('', result)
    return result
