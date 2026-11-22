import xml.etree.ElementTree as ET
import re

_DOCTYPE_RE = re.compile(r"<!\s*(DOCTYPE|ENTITY)", re.IGNORECASE)


def parse_note(xml_text: str) -> str:
    """Parse the XML document in xml_text, whose root element is <note>, and return the
    text content of its <body> child element.
    """
    if isinstance(xml_text, bytes):
        probe = xml_text.decode("utf-8", errors="ignore")
    else:
        probe = xml_text
    if _DOCTYPE_RE.search(probe):
        raise ValueError("DTD and entity declarations are not allowed")

    root = ET.fromstring(xml_text)
    if root.tag != "note":
        raise ValueError("root element must be <note>")
    body = root.find("body")
    if body is None:
        raise ValueError("<note> has no <body> child element")
    return "".join(body.itertext())
