# HAND-WRITTEN RULE-TEST FIXTURE for AST-PATH-001 (not a SecurityEval sample or LLM output).
import os
from pathlib import Path


def read_file_pathlib(base_dir: str, filename: str) -> bytes:
    base = Path(base_dir).resolve()
    target = (base / filename).resolve()
    if not target.is_relative_to(base):
        raise ValueError("outside base")
    return target.read_bytes()


def read_file_commonpath(base_dir, filename):
    base = os.path.realpath(base_dir)
    full = os.path.realpath(os.path.join(base, filename))
    if os.path.commonpath([base, full]) != base:
        raise ValueError("outside base")
    with open(full, "rb") as handle:
        return handle.read()


def read_file_separator_prefix(base_dir, filename):
    prefix = os.path.join(os.path.realpath(base_dir), "")
    full = os.path.realpath(os.path.join(prefix, filename))
    if not full.startswith(prefix):
        raise ValueError("outside base")
    with open(full, "rb") as handle:
        return handle.read()


def _safe_path(base_dir, filename):
    base = Path(base_dir).resolve()
    target = (base / filename).resolve()
    if base not in target.parents:
        raise ValueError("outside base")
    return target


def read_file_with_helper(base_dir, filename):
    with open(_safe_path(base_dir, filename), "rb") as handle:
        return handle.read()


def read_constant_path():
    with open("settings.txt", "rb") as handle:
        return handle.read()
