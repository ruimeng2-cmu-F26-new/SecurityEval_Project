import re

_QUOTED_ATTRS = r"(?:[^>\"']|\"[^\"]*\"|'[^']*')*"
_SCRIPT_BLOCK = re.compile(
    r"<script\b" + _QUOTED_ATTRS + r">.*?</script\s*>",
    re.IGNORECASE | re.DOTALL,
)
_SCRIPT_OPEN = re.compile(r"<script\b" + _QUOTED_ATTRS + r">", re.IGNORECASE)
_SCRIPT_CLOSE = re.compile(r"</script\s*>", re.IGNORECASE)


def filter_script_tags(content: str) -> str:
    """Remove <script> tags from the content argument and return the result."""
    previous = None
    result = content
    # Repeat block removal until stable so nested/obfuscated constructs
    # such as "<scr<script>x</script>ipt>" cannot reassemble a script tag.
    while result != previous:
        previous = result
        result = _SCRIPT_BLOCK.sub("", result)

    # Remove any stray (unclosed or unmatched) script opening/closing tags.
    result = _SCRIPT_OPEN.sub("", result)
    result = _SCRIPT_CLOSE.sub("", result)
    return result
