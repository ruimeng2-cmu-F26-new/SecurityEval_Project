# HAND-WRITTEN RULE-TEST FIXTURE for AST-PATH-001 (not a SecurityEval sample or LLM output).
import os
from pathlib import Path


def read_file_join(base_dir: str, filename: str) -> bytes:
    with open(os.path.join(base_dir, filename), "rb") as handle:  # expect: AST-PATH-001
        return handle.read()


def read_file_pathlib(base_dir, filename):
    return (Path(base_dir) / filename).read_bytes()  # expect: AST-PATH-001


def read_file_dotdot_only(base_dir, filename):
    # Rejecting ".." leaves absolute paths and symlinks.
    if ".." in filename:
        raise ValueError("invalid path")
    path = Path(base_dir) / filename
    return path.open("rb").read()  # expect: AST-PATH-001


def read_file_lexical(base_dir, filename):
    base = os.path.abspath(base_dir)
    full = os.path.abspath(os.path.join(base, filename))
    if not full.startswith(base + os.sep):
        raise ValueError("outside base")
    with open(full, "rb") as handle:  # expect: AST-PATH-001
        return handle.read()


def read_file_prefix(base_dir, filename):
    base = os.path.realpath(base_dir)
    full = os.path.realpath(os.path.join(base, filename))
    if not full.startswith(base):
        raise ValueError("outside base")
    with open(full, "rb") as handle:  # expect: AST-PATH-001
        return handle.read()
