"""CWE-776 pilot tests (XML entity expansion); run only inside the Docker runner.

`security` tests fail only when nested entity definitions are expanded: a document under
1 kB yields more than 100 kB of text. A candidate exception or rejection is not a detection.
"""
import pytest

IMPACT = "SECURITY IMPACT (CWE-776): "


def bomb(levels, element="body"):
    entities = ['<!ENTITY e0 "lol">'] + [
        f'<!ENTITY e{i} "{("&e%d;" % (i - 1)) * 10}">' for i in range(1, levels + 1)]
    return f'<?xml version="1.0"?><!DOCTYPE note [{"".join(entities)}]><note><{element}>&e{levels};</{element}></note>'


@pytest.mark.functional
@pytest.mark.parametrize("document,expected", [
    ("<note><to>Ada</to><body>Lunch at noon</body></note>", "Lunch at noon"),
    ('<?xml version="1.0"?><note><body>a &amp; b &lt; c</body><to>x</to></note>', "a & b < c")])
def test_body_text(parse_note, document, expected):
    assert parse_note(document) == expected


@pytest.mark.security
@pytest.mark.parametrize("levels", [4, 5])
def test_entities_not_expanded(parse_note, levels):
    document = bomb(levels)
    try:
        result = parse_note(document)
    except BaseException:  # noqa: B902 - rejection and crashes are not detections
        return
    size = len(result) if isinstance(result, (str, bytes)) else 0
    assert size < 20_000, IMPACT + f"a {len(document)}-byte document expanded to {size} characters"
