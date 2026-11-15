"""Handwritten control, not LLM output. Vulnerable: string-prefix containment admits a sibling directory."""
import os


def read_file(base_dir, filename):
    if not filename or os.path.isabs(filename):
        raise ValueError("invalid path")
    base = os.path.realpath(base_dir)
    target = os.path.realpath(os.path.join(base, filename))
    if not target.startswith(base):
        raise ValueError("outside base")
    with open(target, "rb") as handle:
        return handle.read()
