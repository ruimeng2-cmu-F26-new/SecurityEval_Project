# HAND-WRITTEN RULE-TEST FIXTURE for AST-CMD-001 (not a SecurityEval sample or LLM output).
# Reported at low severity: the rule sees an allowlist-style comparison but cannot prove it.
import subprocess

ALLOWED = {"pwd", "echo"}


def execute_command_membership(command: str) -> str:
    parts = command.split()
    if not parts or parts[0] not in ALLOWED:
        raise ValueError("unsupported command")
    return subprocess.run(parts, capture_output=True, text=True, timeout=2).stdout  # expect: AST-CMD-001


def execute_command_equality(command: str) -> str:
    parts = command.split()
    program = parts[0]
    if program == "pwd" or program == "echo":
        return subprocess.run(parts, capture_output=True, text=True, timeout=2).stdout  # expect: AST-CMD-001
    raise ValueError("unsupported command")
