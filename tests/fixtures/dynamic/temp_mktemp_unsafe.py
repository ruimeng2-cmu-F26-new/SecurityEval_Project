"""Handwritten control, not LLM output. Vulnerable: mktemp then open; the file is created world-readable."""
import tempfile


def write_results(results):
    path = tempfile.mktemp()
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(results)
    return path
