import re
import xml.etree.ElementTree as ET


_DOCTYPE_RE = re.compile(r"<!\s*(DOCTYPE|ENTITY)", re.IGNORECASE)


class _SafeParser(ET.XMLParser):
    pass


def _reject(*args, **kwargs):
    raise ValueError("DTD and entity declarations are not allowed")


def parse_note(xml_text: str) -> str:
    """Parse the XML document in xml_text, whose root element is <note>, and return the
    text content of its <body> child element.
    """
    if isinstance(xml_text, bytes):
        sample = xml_text.decode("utf-8", errors="ignore")
    else:
        sample = xml_text
    if _DOCTYPE_RE.search(sample):
        raise ValueError("DTD and entity declarations are not allowed")

    parser = ET.XMLParser()
    # Reject any DTD / entity declarations at the parser level as well.
    try:
        parser.parser.StartDoctypeDeclHandler = _reject
        parser.parser.EntityDeclHandler = _reject
        parser.parser.UnparsedEntityDeclHandler = _reject
        parser.parser.ExternalEntityRefHandler = _reject
    except AttributeError:
        pass

    parser.feed(xml_text)
    root = parser.close()
    if root.tag != "note":
        raise ValueError("Root element must be <note>")
    body = root.find("body")
    if body is None:
        return ""
    return "".join(body.itertext())
