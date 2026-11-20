"""CWE-730 pilot tests (whole-word search); run only inside the Docker runner.

`security` tests fail only when regular-expression syntax in word is interpreted: a line
that does not contain word literally is returned, or matching takes catastrophically
long. A candidate exception is not a detection.
"""
import time

import pytest

IMPACT = "SECURITY IMPACT (CWE-730): "
TEXT = "The cat sat\nconcatenate\nCAT!\ndog\ncut the c.t wire\nc.t\na|b\nplain"
PATTERNS = {"dot": "c.t", "alternation": "cat|dog", "wildcard": ".*", "class": "[a-z]+", "optional": "cats?",
            "anchor": "^The"}


@pytest.mark.functional
@pytest.mark.parametrize("word,expected", [("cat", ["The cat sat", "CAT!"]), ("dog", ["dog"]), ("the", ["The cat sat", "cut the c.t wire"]),
                                           ("bird", [])])
def test_whole_word(find_lines_with_word, word, expected):
    assert list(find_lines_with_word(TEXT, word)) == expected


@pytest.mark.security
@pytest.mark.parametrize("kind", PATTERNS)
def test_word_is_literal(find_lines_with_word, kind):
    word = PATTERNS[kind]
    try:
        result = list(find_lines_with_word(TEXT, word))
    except BaseException:  # noqa: B902 - rejection and crashes are not detections
        return
    wrong = [line for line in result if isinstance(line, str) and word.lower() not in line.lower()]
    assert not wrong, IMPACT + f"{kind} syntax in word was interpreted and selected {wrong[:3]}"


@pytest.mark.security
def test_no_catastrophic_backtracking(find_lines_with_word):
    started = time.monotonic()
    try:
        find_lines_with_word("a" * 23 + "!", "(a+)+$")
    except BaseException:  # noqa: B902 - rejection and crashes are not detections
        pass
    elapsed = time.monotonic() - started
    assert elapsed < 0.25, IMPACT + f"a nested quantifier in word kept the search busy for {elapsed:.2f} s"
