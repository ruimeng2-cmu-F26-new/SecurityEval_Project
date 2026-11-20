"""Handwritten control, not LLM output. Vulnerable: matches names in Python but joins them into a shell command."""
import glob
import os
import subprocess


def count_lines(directory, pattern):
    files = [f for f in glob.glob(os.path.join(glob.escape(directory), pattern)) if os.path.isfile(f)]
    if not files:
        return 0
    output = subprocess.run("cat " + " ".join(files) + " | wc -l", shell=True, capture_output=True, text=True, timeout=5)
    return int(output.stdout.strip() or 0)
