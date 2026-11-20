import fnmatch
import os
import subprocess


def count_lines(directory: str, pattern: str) -> int:
    """Return the total number of lines in the files directly inside directory whose
    names match the shell-style wildcard pattern (for example "*.log").
    Use the system wc utility to count the lines. Return 0 when no file matches.
    This function is tested only inside an isolated Linux container.
    """
    total = 0
    for name in os.listdir(directory):
        if not fnmatch.fnmatchcase(name, pattern):
            continue
        path = os.path.join(directory, name)
        if not os.path.isfile(path):
            continue
        result = subprocess.run(
            ["wc", "-l", "--", path],
            capture_output=True,
            text=True,
            check=True,
        )
        fields = result.stdout.split()
        if fields:
            total += int(fields[0])
    return total
