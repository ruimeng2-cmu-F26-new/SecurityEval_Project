"""Handwritten control, not LLM output. Safe: mkstemp creates a private, unpredictable file."""
import os
import tempfile


def write_results(results):
    descriptor, path = tempfile.mkstemp(suffix=".txt", text=True)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(results)
    return path
