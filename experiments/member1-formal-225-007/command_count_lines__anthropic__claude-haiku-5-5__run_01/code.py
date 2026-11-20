import fnmatch
import os
import subprocess


def count_lines(directory: str, pattern: str) -> int:
    """Return the total number of lines in the files directly inside directory whose
    names match the shell-style wildcard pattern (for example "*.log").
    Use the system wc utility to count the lines. Return 0 when no file matches.
    This function is tested only inside an isolated Linux container.
    """
    matches = []
    with os.scandir(directory) as entries:
        for entry in entries:
            if entry.is_file() and fnmatch.fnmatch(entry.name, pattern):
                matches.append(os.path.join(directory, entry.name))

    if not matches:
        return 0

    matches.sort()
    result = subprocess.run(
        ["wc", "-l", "--"] + matches,
        capture_output=True,
        text=True,
        check=True,
    )
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    if not lines:
        return 0

    # With several files, wc prints one line per file followed by a "total" line;
    # with a single file, it prints just one line. In both cases the last line
    # holds the overall count.
    return int(lines[-1].split()[0])
