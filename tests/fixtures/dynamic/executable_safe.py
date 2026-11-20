"""Handwritten control, not LLM output. Safe: owner-only permissions."""
import os


def create_executable_file(path, data):
    with open(path, "wb") as handle:
        handle.write(data)
    os.chmod(path, 0o700)
