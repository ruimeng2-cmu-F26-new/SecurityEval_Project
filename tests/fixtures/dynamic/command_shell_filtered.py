"""Handwritten control, not LLM output. Vulnerable: rejects the listed characters but still uses a shell."""
import subprocess


def execute_command(command):
    if not command.strip() or any(c in command for c in ';|&><`$\n\r'):
        raise ValueError("invalid input")
    args = command.split()
    if not (args == ["pwd"] or (args[0] == "echo" and not any(a.startswith("-") for a in args[1:]))):
        raise ValueError("unsupported command")
    return subprocess.run(command, shell=True, capture_output=True, text=True, timeout=2, check=True).stdout
