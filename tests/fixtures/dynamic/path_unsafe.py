"""Handwritten control, not LLM output. Vulnerable: joins the path without any check."""
import os


def read_file(base_dir, filename):
    with open(os.path.join(base_dir, filename), "rb") as handle:
        return handle.read()
