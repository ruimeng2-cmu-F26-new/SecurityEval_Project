"""Handwritten control, not LLM output. Vulnerable: default parser expands nested entities."""
import xml.etree.ElementTree as ET


def parse_note(xml_text):
    return ET.fromstring(xml_text).findtext("body") or ""
