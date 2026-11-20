"""Handwritten control, not LLM output. Safe: refuses documents that declare a DTD or entities."""
import xml.etree.ElementTree as ET


def parse_note(xml_text):
    if "<!DOCTYPE" in xml_text.upper() or "<!ENTITY" in xml_text.upper():
        raise ValueError("DTD is not allowed")
    return ET.fromstring(xml_text).findtext("body") or ""
