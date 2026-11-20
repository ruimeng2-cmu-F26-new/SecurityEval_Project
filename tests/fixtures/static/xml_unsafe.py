# HAND-WRITTEN RULE-TEST FIXTURE for AST-XML-001 (not a SecurityEval sample or LLM output).
import xml.etree.ElementTree as ET
from xml.dom import minidom
from xml.etree.ElementTree import fromstring


def body(xml_text):
    return ET.fromstring(xml_text).findtext("body")  # expect: AST-XML-001


def imported_name(xml_text):
    root = fromstring(xml_text.strip())  # expect: AST-XML-001
    return root.tag


def dom(xml_text):
    return minidom.parseString(xml_text).documentElement.tagName  # expect: AST-XML-001


def from_file(path):
    return ET.parse(path).getroot()  # expect: AST-XML-001
