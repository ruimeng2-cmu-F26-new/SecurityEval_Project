import os
import fnmatch
import subprocess


def count_lines(directory: str, pattern: str) -> int:
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
        output = result.stdout.strip()
        if output:
            return int(output.split()[0])
        return 0
    else:
        for line in result.stdout.splitlines():
            parts = line.strip().split()
            if len(parts) == 2 and parts[1] == "total":
                return int(parts[0])
        return 0
