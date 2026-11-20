# HAND-WRITTEN RULE-TEST FIXTURE for AST-PERM-001 (not a SecurityEval sample or LLM output).
import os
import stat
from pathlib import Path


def world_writable(path):
    os.chmod(path, 0o777)  # expect: AST-PERM-001


def group_writable(path):
    Path(path).chmod(0o775)  # expect: AST-PERM-001


def symbolic(path):
    os.chmod(path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)  # expect: AST-PERM-001


def at_creation(data):
    descriptor = os.open("tool.bin", os.O_WRONLY | os.O_CREAT, 0o766)  # expect: AST-PERM-001
    os.write(descriptor, data)
    os.close(descriptor)


def cleared_mask(path):
    os.umask(0)  # expect: AST-PERM-001
    os.chmod(path, mode=0o757)  # expect: AST-PERM-001
