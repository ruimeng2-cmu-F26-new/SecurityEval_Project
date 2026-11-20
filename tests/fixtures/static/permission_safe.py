# HAND-WRITTEN RULE-TEST FIXTURE for AST-PERM-001 (not a SecurityEval sample or LLM output).
import os
import stat
from pathlib import Path


def owner_only(path):
    os.chmod(path, 0o700)


def readable(path):
    Path(path).chmod(0o755)


def add_execute(path):
    current = os.stat(path).st_mode
    os.chmod(path, current | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def masked(path):
    os.chmod(path, os.stat(path).st_mode & 0o755)


def at_creation():
    os.close(os.open("tool.bin", os.O_WRONLY | os.O_CREAT, 0o700))
    os.umask(0o077)
