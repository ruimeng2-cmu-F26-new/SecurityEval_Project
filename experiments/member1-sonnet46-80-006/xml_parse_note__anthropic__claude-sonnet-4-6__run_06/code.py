import xml.etree.ElementTree as ET

def parse_note(xml_text: str) -> str:
    """Parse the XML document in xml_text, whose root element is <note>, and return the
    text content of its <body> child element.
    """
    root = ET.fromstring(xml_text)
    body = root.find('body')
    if body is None:
        raise ValueError("No <body> element found in <note>")
    return body.text or ''
