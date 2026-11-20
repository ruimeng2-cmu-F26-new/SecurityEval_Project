"""Handwritten control, not LLM output. Vulnerable: uses the word as a regular expression."""
import re


def find_lines_with_word(text, word):
    pattern = re.compile(r"\b" + word + r"\b", re.IGNORECASE)
    return [line for line in text.splitlines() if pattern.search(line)]
