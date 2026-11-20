# HAND-WRITTEN RULE-TEST FIXTURE for AST-XML-001 (not a SecurityEval sample or LLM output).
import xml.etree.ElementTree as ET


def constant_document():
    return ET.fromstring("<note><body>fixed</body></note>").findtext("body")


def build(text):
    root = ET.Element("note")
    ET.SubElement(root, "body").text = text
    return ET.tostring(root)
