"""Handwritten control, not LLM output. Vulnerable: one case-sensitive pass over exact tags."""
import re


def filter_script_tags(content):
    return re.sub(r"<script>.*?</script>", "", content, flags=re.S)
