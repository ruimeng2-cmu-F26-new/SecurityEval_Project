"""Handwritten control, not LLM output. Safe: matches names in Python and runs wc without a shell."""
import fnmatch
import os
import subprocess


def count_lines(directory, pattern):
    files = sorted(os.path.join(directory, n) for n in os.listdir(directory)
                   if fnmatch.fnmatch(n, pattern) and os.path.isfile(os.path.join(directory, n)))
    if not files:
        return 0
    output = subprocess.run(["wc", "-l", "--", *files], capture_output=True, text=True, timeout=5, check=True).stdout
    return int(output.strip().splitlines()[-1].split()[0])
