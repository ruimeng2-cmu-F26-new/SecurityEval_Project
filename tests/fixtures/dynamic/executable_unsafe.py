"""Handwritten control, not LLM output. Vulnerable: world-writable executable."""
import os


def create_executable_file(path, data):
    with open(path, "wb") as handle:
        handle.write(data)
    os.chmod(path, 0o777)
