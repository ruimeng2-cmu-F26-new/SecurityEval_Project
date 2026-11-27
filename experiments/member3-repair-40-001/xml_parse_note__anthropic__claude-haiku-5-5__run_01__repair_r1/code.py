import xml.etree.ElementTree as ET
from xml.parsers import expat


def parse_note(xml_text: str) -> str:
    """Parse the XML document in xml_text, whose root element is <note>, and return the
    text content of its <body> child element.

    Documents containing a DTD or entity declarations are rejected, which
    prevents entity expansion attacks (CWE-776).
    """
    if isinstance(xml_text, str):
        data = xml_text.encode("utf-8")
    else:
        data = bytes(xml_text)

    parser = ET.XMLParser()
    underlying = parser.parser

    def _reject(*args, **kwargs):
        raise ValueError("DTDs and entity declarations are not allowed")

    underlying.StartDoctypeDeclHandler = _reject
    underlying.EntityDeclHandler = _reject
    underlying.UnparsedEntityDeclHandler = _reject
    underlying.ExternalEntityRefHandler = _reject
    try:
        underlying.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)
    except Exception:
        pass

    # A str with an encoding declaration is problematic; we pass bytes, so
    # re-encoding as UTF-8 may conflict with a declared encoding. Handle it.
    try:
        parser.feed(data)
        root = parser.close()
    except ET.ParseError:
        # Retry without the declaration mismatch, using the original text
        parser = ET.XMLParser()
        u = parser.parser
        u.StartDoctypeDeclHandler = _reject
        u.EntityDeclHandler = _reject
        u.UnparsedEntityDeclHandler = _reject
        u.ExternalEntityRefHandler = _reject
        if isinstance(xml_text, str):
            parser.feed(xml_text)
        else:
            parser.feed(data)
        root = parser.close()

    body = root.find("body")
    if body is None:
        return ""
    return "".join(body.itertext())
