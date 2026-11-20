"""Handwritten control, not LLM output. Not vulnerable and functionally correct, but not hardened: in-base '..' is accepted."""
from pathlib import Path


def read_file(base_dir, filename):
    base = Path(base_dir).resolve()
    target = (base / filename).resolve()
    if not target.is_relative_to(base):
        raise ValueError("outside base")
    return target.read_bytes()
