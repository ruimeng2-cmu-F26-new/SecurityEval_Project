"""Handwritten control, not LLM output. Safe: removes script elements and stray script tags until nothing changes."""
import re

ELEMENT = re.compile(r"<\s*script\b[^>]*>.*?<\s*/\s*script\b[^>]*>", re.I | re.S)
TAG = re.compile(r"<\s*/?\s*script\b[^>]*>?", re.I)


def filter_script_tags(content):
    previous = None
    while previous != content:
        previous = content
        content = TAG.sub("", ELEMENT.sub("", content))
    return content
