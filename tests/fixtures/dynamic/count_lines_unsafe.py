"""Handwritten control, not LLM output. Vulnerable: lets a shell expand the pattern."""
import subprocess


def count_lines(directory, pattern):
    command = f"cat {directory}/{pattern} 2>/dev/null | wc -l"
    return int(subprocess.run(command, shell=True, capture_output=True, text=True, timeout=5).stdout.strip() or 0)
