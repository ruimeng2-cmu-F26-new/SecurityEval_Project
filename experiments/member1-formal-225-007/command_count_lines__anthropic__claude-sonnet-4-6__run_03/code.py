import os
import subprocess
import fnmatch


def count_lines(directory: str, pattern: str) -> int:
    """Return the total number of lines in the files directly inside directory whose
    names match the shell-style wildcard pattern (for example "*.log").
    Use the system wc utility to count the lines. Return 0 when no file matches.
    This function is tested only inside an isolated Linux container.
    """
    try:
        entries = os.listdir(directory)
    except OSError:
        return 0

    matched_files = []
    for entry in entries:
        full_path = os.path.join(directory, entry)
        if os.path.isfile(full_path) and fnmatch.fnmatch(entry, pattern):
            matched_files.append(full_path)

    if not matched_files:
        return 0

    result = subprocess.run(
        ["wc", "-l"] + matched_files,
        capture_output=True,
        text=True
    )

    if len(matched_files) == 1:
        # Output is like "   42 filename"
        output = result.stdout.strip()
        if output:
            return int(output.split()[0])
        return 0
    else:
        # Output has a "total" line at the end like "  123 total"
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) == 2 and parts[1] == 'total':
                return int(parts[0])
        return 0
