import re

_ATTRS = r'''(?:[^>"']|"[^"]*"|'[^']*')*'''

_BLOCK = re.compile(
    r'<script\b' + _ATTRS + r'>.*?(?:</script\b' + _ATTRS + r'>|\Z)',
    re.IGNORECASE | re.DOTALL,
)
_STRAY = re.compile(
    r'</?script\b' + _ATTRS + r'(?:>|\Z)',
    re.IGNORECASE | re.DOTALL,
)


def filter_script_tags(content: str) -> str:
    """Remove <script> tags from the content argument and return the result."""
    previous = None
    while previous != content:
        previous = content
        content = _BLOCK.sub('', content)
        content = _STRAY.sub('', content)
    return content
