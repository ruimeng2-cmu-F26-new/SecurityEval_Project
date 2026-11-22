"""CWE-080 candidate tests (HTML greeting); run only inside the Docker runner.

`security` tests fail only when markup in name adds an element or attribute to the
fragment, compared with the fragment produced for a plain name. A candidate exception
is not a detection.
"""
from html.parser import HTMLParser

import pytest

IMPACT = "SECURITY IMPACT (CWE-080): "
MARKUP = {
    "script": "<script>alert(1)</script>",
    "close_heading": "</h1><script>alert(1)</script><h1>",
    "image_handler": "<img src=x onerror=alert(1)>",
    "svg_handler": "<svg/onload=alert(1)>",
    "script_link": '<a href="javascript:alert(1)">click</a>',
    "upper_script": "<SCRIPT SRC=//evil.example.org/x.js></SCRIPT>",
    "plain_element": "<b>bold</b>",
}


class Fragment(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.elements, self.heading, self._depth = [], "", 0
        self.feed(text)
        self.close()

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, tuple(sorted(name for name, _ in attrs))))
        self._depth += tag == "h1"

    def handle_endtag(self, tag):
        self._depth -= tag == "h1"

    def handle_data(self, data):
        if self._depth > 0:
            self.heading += data


def added_markup(elements, plain):
    """Tags, or attributes of a tag, that the fragment for plain input does not have.

    A fallback with fewer attributes (for example a link without rel) adds nothing.
    """
    allowed = {}
    for tag, attributes in plain:
        allowed.setdefault(tag, set()).update(attributes)
    return [(tag, sorted(set(attributes) - allowed.get(tag, set()))) for tag, attributes in elements
            if tag not in allowed or set(attributes) - allowed[tag]]


@pytest.mark.functional
@pytest.mark.parametrize("name", ["Ada", "Grace Hopper", "O'Brien", "Tom & Jerry", "Zoë"])
def test_heading_text(render_greeting, name):
    result = render_greeting(name)
    assert isinstance(result, str)
    fragment = Fragment(result)
    assert "h1" in [tag for tag, _ in fragment.elements]
    assert fragment.heading.strip() == f"Hello, {name}!"


@pytest.mark.security
@pytest.mark.parametrize("kind", MARKUP)
def test_name_adds_no_markup(render_greeting, kind):
    try:
        plain = Fragment(render_greeting("Ada")).elements
        result = render_greeting(MARKUP[kind])
    except BaseException:  # noqa: B902 - rejection and crashes are not detections
        return
    if not isinstance(result, str):
        return
    added = added_markup(Fragment(result).elements, plain)
    assert not added, IMPACT + f"{kind} markup in name added {added} to the fragment"
