import re
from html.parser import HTMLParser


class _ScriptStripper(HTMLParser):
    """Rebuilds the document while dropping <script> elements and their content."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.out: list[str] = []
        self.depth = 0

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "script":
            self.depth += 1
            return
        if self.depth == 0:
            self.out.append(self.get_starttag_text())

    def handle_startendtag(self, tag, attrs):
        if tag.lower() == "script":
            return
        if self.depth == 0:
            self.out.append(self.get_starttag_text())

    def handle_endtag(self, tag):
        if tag.lower() == "script":
            if self.depth > 0:
                self.depth -= 1
            return
        if self.depth == 0:
            self.out.append("</%s>" % tag)

    def handle_data(self, data):
        if self.depth == 0:
            self.out.append(data)

    def handle_entityref(self, name):
        if self.depth == 0:
            self.out.append("&%s;" % name)

    def handle_charref(self, name):
        if self.depth == 0:
            self.out.append("&#%s;" % name)

    def handle_comment(self, data):
        if self.depth == 0:
            self.out.append("<!--%s-->" % data)

    def handle_decl(self, decl):
        if self.depth == 0:
            self.out.append("<!%s>" % decl)

    def handle_pi(self, data):
        if self.depth == 0:
            self.out.append("<?%s>" % data)

    def unknown_decl(self, data):
        if self.depth == 0:
            self.out.append("<![%s]>" % data)


def _strip_once(content: str) -> str:
    parser = _ScriptStripper()
    parser.feed(content)
    parser.close()
    return "".join(parser.out)


def filter_script_tags(content: str) -> str:
    """Remove <script> tags from the content argument and return the result."""
    result = content
    # Repeat until stable so reassembled/nested constructs cannot survive.
    for _ in range(20):
        new = _strip_once(result)
        if new == result:
            break
        result = new
    # Final safeguard: neutralize any leftover script tag openers/closers.
    result = re.sub(r"<\s*/?\s*script", "", result, flags=re.IGNORECASE)
    return result
