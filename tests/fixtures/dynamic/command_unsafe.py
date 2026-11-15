"""Handwritten control, not LLM output. Vulnerable: passes input to a shell."""
import subprocess


def execute_command(command):
    return subprocess.run(command, shell=True, capture_output=True, text=True, timeout=2).stdout
