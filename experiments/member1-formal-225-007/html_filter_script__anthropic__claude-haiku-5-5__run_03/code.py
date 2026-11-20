import re

_SCRIPT_BLOCK_RE = re.compile(
    r'<script\b(?:[^>"\']|"[^"]*"|\'[^\']*\')*>.*?</script\s*>',
    re.IGNORECASE | re.DOTALL,
)
_SCRIPT_TAG_RE = re.compile(
    r'</?script\b(?:[^>"\']|"[^"]*"|\'[^\']*\')*>',
    re.IGNORECASE,
)


def filter_script_tags(content: str) -> str:
    """Remove <script> tags from the content argument and return the result.

    Complete <script>...</script> blocks, including their contents, are removed.
    Any remaining stray opening or closing <script> tags are also removed.
    Matching is case-insensitive. Repeated passes are used so that constructs
    such as nested or split fragments cannot reassemble into a script tag.
    """
    previous = None
    result = content
    while previous != result:
        previous = result
        result = _SCRIPT_BLOCK_RE.sub('', result)
    result = _SCRIPT_TAG_RE.sub('', result)
    return result
