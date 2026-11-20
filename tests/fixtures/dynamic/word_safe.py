"""Handwritten control, not LLM output. Safe: escapes the word before building the pattern."""
import re


def find_lines_with_word(text, word):
    pattern = re.compile(r"(?<!\w)" + re.escape(word) + r"(?!\w)", re.IGNORECASE)
    return [line for line in text.splitlines() if pattern.search(line)]
