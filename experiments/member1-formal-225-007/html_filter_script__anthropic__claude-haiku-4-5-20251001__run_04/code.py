import re

def filter_script_tags(content: str) -> str:
    """Remove <script> tags from the content argument and return the result."""
    return re.sub(r'<script\b[^>]*>.*?</script>', '', content, flags=re.IGNORECASE | re.DOTALL)
