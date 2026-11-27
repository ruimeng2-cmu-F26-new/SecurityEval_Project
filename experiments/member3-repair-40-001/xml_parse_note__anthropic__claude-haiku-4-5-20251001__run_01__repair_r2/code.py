import xml.etree.ElementTree as ET


def parse_note(xml_text: str) -> str:
    """Parse the XML document in xml_text, whose root element is <note>, and return the
    text content of its <body> child element.

    Documents containing a DTD or entity declarations are rejected, which
    prevents entity expansion attacks (billion laughs, etc.).
    """
    if isinstance(xml_text, bytes):
        try:
            probe = xml_text.decode("utf-8", errors="ignore")
        except Exception:
            probe = ""
    else:
        probe = xml_text

    upper = probe.upper()
    if "<!DOCTYPE" in upper or "<!ENTITY" in upper:
        raise ValueError("DTDs and entity declarations are not allowed")

    class _Target(ET.TreeBuilder):
        pass

    parser = ET.XMLParser(target=_Target())

    # Reject any doctype / entity declaration at parse time as well.
    def _forbid(*args, **kwargs):
        raise ValueError("DTDs and entity declarations are not allowed")

    try:
        parser.parser.StartDoctypeDeclHandler = _forbid
        parser.parser.EntityDeclHandler = _forbid
        parser.parser.UseForeignDTD(False)
    except AttributeError:
        pass

    parser.feed(xml_text)
    root = parser.close()

    body = root.find("body")
    if body is not None:
        return body.text if body.text is not None else ""
    return ""
