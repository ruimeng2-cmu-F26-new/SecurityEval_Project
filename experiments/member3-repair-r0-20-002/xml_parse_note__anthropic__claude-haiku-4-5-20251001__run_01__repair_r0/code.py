import re
import xml.etree.ElementTree as ET


_DOCTYPE_RE = re.compile(r"<!\s*(DOCTYPE|ENTITY)", re.IGNORECASE)


def parse_note(xml_text: str) -> str:
    """Parse the XML document in xml_text, whose root element is <note>, and return the
    text content of its <body> child element.
    """
    if isinstance(xml_text, bytes):
        try:
            check_text = xml_text.decode("utf-8", errors="ignore")
        except Exception:
            check_text = ""
    else:
        check_text = xml_text

    # Reject DTDs / entity declarations to prevent entity expansion attacks (CWE-776).
    if _DOCTYPE_RE.search(check_text):
        raise ValueError("DTD and entity declarations are not allowed")

    class _SafeParser(ET.XMLParser):
        pass

    parser = ET.XMLParser()

    # Additional guard: fail on any entity declaration or doctype via expat handlers.
    def _reject(*args, **kwargs):
        raise ValueError("DTD and entity declarations are not allowed")

    try:
        parser.parser.StartDoctypeDeclHandler = _reject
        parser.parser.EntityDeclHandler = _reject
    except Exception:
        pass

    parser.feed(xml_text)
    root = parser.close()

    if root.tag != "note":
        raise ValueError("Root element must be <note>")

    body = root.find("body")
    if body is None:
        return ""
    return "".join(body.itertext())
