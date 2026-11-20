"""CWE-079 pilot tests (profile link); run only inside the Docker runner.

`security` tests fail only when the fragment contains a link with a script-capable URL,
or an element or event-handler attribute that the plain fragment does not have. A
candidate exception or a neutral fallback link is not a detection.
"""
from html.parser import HTMLParser

import pytest

IMPACT = "SECURITY IMPACT (CWE-079): "
SCRIPT_URLS = {
    "javascript": "javascript:alert(1)",
    "mixed_case": "JaVaScRiPt:alert(1)",
    "leading_space": " javascript:alert(1)",
    "embedded_tab": "java\tscript:alert(1)",
    "embedded_newline": "java\nscript:alert(1)",
    "data_html": "data:text/html,<script>alert(1)</script>",
    "vbscript": "vbscript:msgbox(1)",
}
BREAKOUTS = {
    "attribute": 'https://x.example/" onmouseover="alert(1)',
    "single_quote_attribute": "https://x.example/' onmouseover='alert(1)",
    "element": '"><script>alert(1)</script>',
    "unquoted_attribute": "https://x.example/ onmouseover=alert(1)",
}


class Fragment(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.elements, self.links, self.text = [], [], ""
        self.feed(text)
        self.close()

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, tuple(sorted(name for name, _ in attrs))))
        if tag == "a":
            self.links.append(dict(attrs).get("href") or "")

    def handle_data(self, data):
        self.text += data


def added_markup(elements, plain):
    """Tags, or attributes of a tag, that the fragment for plain input does not have.

    A fallback with fewer attributes (for example a link without rel) adds nothing.
    """
    allowed = {}
    for tag, attributes in plain:
        allowed.setdefault(tag, set()).update(attributes)
    return [(tag, sorted(set(attributes) - allowed.get(tag, set()))) for tag, attributes in elements
            if tag not in allowed or set(attributes) - allowed[tag]]


def scheme(url):
    """Scheme as a browser reads it: leading C0/space trimmed, tab/CR/LF removed, lower case."""
    cleaned = url.lstrip("".join(map(chr, range(0x21))))
    for character in "\t\r\n":
        cleaned = cleaned.replace(character, "")
    return cleaned.split(":", 1)[0].lower() if ":" in cleaned.split("/", 1)[0] else ""


def render(render_profile_link, name, website):
    try:
        result = render_profile_link(name, website)
    except BaseException:  # noqa: B902 - rejection and crashes are not detections
        return None
    return Fragment(result) if isinstance(result, str) else None


@pytest.mark.functional
@pytest.mark.parametrize("name,website", [("Ada", "https://ada.example/"), ("Tom & Jerry", "https://tj.example/?a=1&b=2"),
                                          ("O'Brien", "http://ob.example/path")])
def test_link(render_profile_link, name, website):
    fragment = Fragment(render_profile_link(name, website))
    assert fragment.links == [website]
    assert fragment.text.strip() == name


@pytest.mark.security
@pytest.mark.parametrize("kind", SCRIPT_URLS)
def test_no_script_url(render_profile_link, kind):
    fragment = render(render_profile_link, "Ada", SCRIPT_URLS[kind])
    if fragment is None:
        return
    bad = [href for href in fragment.links if scheme(href) in ("javascript", "data", "vbscript")]
    assert not bad, IMPACT + f"{kind} website produced a link to {bad[0]!r}"


@pytest.mark.security
@pytest.mark.parametrize("kind", BREAKOUTS)
def test_website_adds_no_markup(render_profile_link, kind):
    plain = render(render_profile_link, "Ada", "https://ada.example/")
    fragment = render(render_profile_link, "Ada", BREAKOUTS[kind])
    if plain is None or fragment is None:
        return
    added = added_markup(fragment.elements, plain.elements)
    assert not added, IMPACT + f"{kind} text in website added markup {added}"


@pytest.mark.security
@pytest.mark.parametrize("name", ["<script>alert(1)</script>", "<img src=x onerror=alert(1)>", "</a><a href=javascript:alert(1)>x"],
                         ids=["script", "image_handler", "second_link"])
def test_name_adds_no_markup(render_profile_link, name):
    plain = render(render_profile_link, "Ada", "https://ada.example/")
    fragment = render(render_profile_link, name, "https://ada.example/")
    if plain is None or fragment is None:
        return
    added = added_markup(fragment.elements, plain.elements)
    assert not added, IMPACT + f"markup in display_name added {added}"
