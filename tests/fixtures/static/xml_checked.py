# HAND-WRITTEN RULE-TEST FIXTURE for AST-XML-001 (not a SecurityEval sample or LLM output).
import xml.etree.ElementTree as ET


def body(xml_text):
    if "<!DOCTYPE" in xml_text.upper() or "<!ENTITY" in xml_text.upper():
        raise ValueError("DTD is not allowed")
    return ET.fromstring(xml_text).findtext("body")  # expect: AST-XML-001
