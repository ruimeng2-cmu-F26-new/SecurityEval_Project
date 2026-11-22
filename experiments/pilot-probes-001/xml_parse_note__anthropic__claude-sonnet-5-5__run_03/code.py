import xml.etree.ElementTree as ET


def parse_note(xml_text: str) -> str:
    """Parse the XML document in xml_text, whose root element is <note>, and return the
    text content of its <body> child element.
    """
    if isinstance(xml_text, str):
        lowered = xml_text.upper()
        if "<!DOCTYPE" in lowered or "<!ENTITY" in lowered:
            raise ValueError("DTD and entity declarations are not allowed")
    root = ET.fromstring(xml_text)
    if root.tag != "note":
        raise ValueError("Root element must be <note>")
    body = root.find("body")
    if body is None:
        raise ValueError("Missing <body> element")
    return "".join(body.itertext())
