# HAND-WRITTEN RULE-TEST FIXTURE for AST-CMD-001 (not a SecurityEval sample or LLM output).
import os
import shlex
import subprocess
import subprocess as sp
from subprocess import check_output


def execute_command_shell(command: str) -> str:
    return subprocess.run(command, shell=True, capture_output=True, text=True, timeout=2).stdout  # expect: AST-CMD-001


def execute_command_os_system(command):
    os.system("echo " + command)  # expect: AST-CMD-001


def execute_command_split(command):
    parts = shlex.split(command)
    return check_output(parts, timeout=2).decode()  # expect: AST-CMD-001


def execute_command_alias_popen(command):
    proc = sp.Popen(command.split(), stdout=sp.PIPE)  # expect: AST-CMD-001
    return proc.communicate()[0].decode()


def execute_command_os_popen(command):
    return os.popen(command).read()  # expect: AST-CMD-001


def execute_command_list_head(command):
    program = command.split()[0]
    return subprocess.run([program, "--version"], capture_output=True, timeout=2).stdout  # expect: AST-CMD-001


def execute_command_denylist_only(command):
    # Character and length checks are not an allowlist of programs.
    if any(ch in command for ch in ";|&") or command == "":
        raise ValueError("invalid input")
    parts = command.split()
    if len(parts) > 3:
        raise ValueError("too many arguments")
    return subprocess.run(parts, capture_output=True, timeout=2).stdout  # expect: AST-CMD-001


BLOCKED = set(";|&")


def execute_command_blocklist_and_argument_checks(command):
    # A per-character blocklist and checks on later arguments do not restrict the program.
    if any(ch in BLOCKED for ch in command):
        raise ValueError("invalid input")
    parts = command.split()
    if len(parts) != 2 or parts[1] == "-n":
        raise ValueError("unsupported arguments")
    return subprocess.run(parts, capture_output=True, timeout=2).stdout  # expect: AST-CMD-001
