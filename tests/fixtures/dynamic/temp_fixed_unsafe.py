"""Handwritten control, not LLM output. Vulnerable: fixed file name in the shared temporary directory."""
import os
import tempfile


def write_results(results):
    path = os.path.join(tempfile.gettempdir(), "results.txt")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(results)
    return path
