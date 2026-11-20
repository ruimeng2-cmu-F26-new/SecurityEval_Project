# HAND-WRITTEN RULE-TEST FIXTURE for AST-FILTER-001 (not a SecurityEval sample or LLM output).
import re
from html.parser import HTMLParser


class Remover(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.parts, self.skipping = [], 0

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            self.skipping += 1
        elif not self.skipping:
            self.parts.append(self.get_starttag_text())

    def handle_endtag(self, tag):
        if tag == "script":
            self.skipping = max(0, self.skipping - 1)
        elif not self.skipping:
            self.parts.extend(("</", tag, ">"))

    def handle_data(self, data):
        if not self.skipping:
            self.parts.append(data)


def filter_script_tags(content):
    remover = Remover()
    remover.feed(content)
    remover.close()
    return "".join(remover.parts)


def collapse_spaces(content):
    return re.sub(r"\s+", " ", content.replace("\t", " "))
