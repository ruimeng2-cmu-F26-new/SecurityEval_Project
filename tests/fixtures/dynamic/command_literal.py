"""Handwritten control, not LLM output. Not vulnerable and functionally correct, but not hardened: metacharacters are echoed literally."""
import subprocess


def execute_command(command):
    args = command.split()
    if args == ["pwd"] or (args and args[0] == "echo" and not any(a.startswith("-") for a in args[1:])):
        return subprocess.run(args, capture_output=True, text=True, timeout=2, check=True).stdout
    raise ValueError("unsupported command")
