# HAND-WRITTEN RULE-TEST FIXTURE for AST-FILTER-001 (not a SecurityEval sample or LLM output).
import re

PATTERN = re.compile(r"<script.*?>.*?</script>", re.I | re.S)  # expect: AST-FILTER-001
OPENING = r"<\s*script[^>]*>"


def exact(content):
    return re.sub(r"<script>.*?</script>", "", content, flags=re.S)  # expect: AST-FILTER-001


def compiled(content):
    return PATTERN.sub("", content)


def named_pattern(content):
    return re.sub(OPENING, "", content)  # expect: AST-FILTER-001


def fixed_strings(content):
    return content.replace("<script>", "").replace("</script>", "")  # expect: AST-FILTER-001
