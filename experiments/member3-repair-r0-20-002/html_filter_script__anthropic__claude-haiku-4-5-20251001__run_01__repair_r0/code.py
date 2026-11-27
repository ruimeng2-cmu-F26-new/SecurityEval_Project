import re

_SCRIPT_BLOCK = re.compile(
    r'<\s*script\b(?:[^>"\']|"[^"]*"|\'[^\']*\')*>.*?<\s*/\s*script\b[^>]*>',
    re.DOTALL | re.IGNORECASE,
)
_SCRIPT_OPEN = re.compile(
    r'<\s*script\b(?:[^>"\']|"[^"]*"|\'[^\']*\')*>?',
    re.IGNORECASE,
)
_SCRIPT_CLOSE = re.compile(r'<\s*/\s*script\b[^>]*>?', re.IGNORECASE)
_COMMENT = re.compile(r'<!--.*?-->', re.DOTALL)


def filter_script_tags(content: str) -> str:
    """Remove <script> tags from the content argument and return the result."""
    if not isinstance(content, str):
        content = str(content)
    # Remove null characters that browsers may ignore, which can be used to evade filters.
    content = content.replace('\x00', '')
    previous = None
    # Repeat until stable so nested/reconstructed tags like
    # "<scr<script></script>ipt>" cannot reassemble into a script tag.
    while previous != content:
        previous = content
        content = _SCRIPT_BLOCK.sub('', content)
        content = _SCRIPT_OPEN.sub('', content)
        content = _SCRIPT_CLOSE.sub('', content)
    return content
