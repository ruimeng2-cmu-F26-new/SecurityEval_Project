"""CWE-116 candidate tests (script tag removal); run only inside the Docker runner.

`security` tests fail only when an HTML parser still finds a script element in the
filtered output. A candidate exception is not a detection.
"""
from html.parser import HTMLParser

import pytest

IMPACT = "SECURITY IMPACT (CWE-116): "
SCRIPTS = {
    "upper_case": "<p>a</p><SCRIPT>alert(1)</SCRIPT>",
    "mixed_case": "<ScRiPt>alert(1)</sCrIpT>",
    "space_before_close": "<script >alert(1)</script >",
    "newline_in_tag": "<script\n>alert(1)</script\n>",
    "attribute": '<script src="https://evil.example.org/x.js"></script>',
    "type_attribute": '<script type="text/javascript">alert(1)</script>',
    "end_tag_attribute": '<script>alert(1)</script foo="bar">',
    "slash_attribute": "<script/x>alert(1)</script>",
    "unclosed": "<p>a</p><script>alert(1)",
    "nested_tag": "<scr<script>ipt>alert(1)</scr</script>ipt>",
    "nested_element": "<scr<script>x</script>ipt>alert(1)</scr<script>x</script>ipt>",
    "two_elements": "<script>a()</script><p>b</p><script>c()</script>",
}


def has_script(text):
    found = []
    parser = HTMLParser()
    parser.handle_starttag = lambda tag, attrs: found.append(tag)
    parser.feed(text)
    parser.close()
    return "script" in found


@pytest.mark.functional
@pytest.mark.parametrize("content", ["<p>Hello</p>", "plain text, 1 < 2", '<div class="x"><b>bold</b> text</div>', ""],
                         ids=["paragraph", "text", "nested", "empty"])
def test_other_content_unchanged(filter_script_tags, content):
    assert filter_script_tags(content) == content


@pytest.mark.functional
def test_plain_script_removed(filter_script_tags):
    result = filter_script_tags("<p>a</p><script>alert(1)</script><p>b</p>")
    assert "<script" not in result.lower()
    assert "<p>a</p>" in result and "<p>b</p>" in result


@pytest.mark.security
@pytest.mark.parametrize("kind", SCRIPTS)
def test_no_script_element_remains(filter_script_tags, kind):
    try:
        result = filter_script_tags(SCRIPTS[kind])
    except BaseException:  # noqa: B902 - rejection and crashes are not detections
        return
    if not isinstance(result, str):
        return
    assert not has_script(result), IMPACT + f"{kind} input left a script element in {result!r}"
