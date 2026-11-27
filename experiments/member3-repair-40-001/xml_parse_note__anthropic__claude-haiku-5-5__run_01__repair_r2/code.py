import re
import xml.etree.ElementTree as ET


def parse_note(xml_text: str) -> str:
    """Parse the XML document in xml_text, whose root element is <note>, and return the
    text content of its <body> child element.
    """
    if isinstance(xml_text, bytes):
        sample = xml_text.decode("utf-8", errors="ignore")
    else:
        sample = xml_text

    # Reject any DTD / entity declarations outright to prevent entity expansion attacks.
    if re.search(r"<!\s*(DOCTYPE|ENTITY)", sample, re.IGNORECASE):
        raise ValueError("DTD and entity declarations are not allowed")

    parser = ET.XMLParser()
    # Belt and braces: refuse any doctype/entity declaration seen by the parser.
    def _forbid(*args, **kwargs):
        raise ValueError("DTD and entity declarations are not allowed")

    try:
        parser.parser.EntityDeclHandler = _forbid
        parser.parser.StartDoctypeDeclHandler = _forbid
    except AttributeError:
        pass

    parser.feed(xml_text)
    root = parser.close()

    body = root.find("body")
    if body is None:
        return ""
    return "".join(body.itertext())
