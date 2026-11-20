import fnmatch
import os
import subprocess


def count_lines(directory: str, pattern: str) -> int:
    """Return the total number of lines in the files directly inside directory whose
    names match the shell-style wildcard pattern (for example "*.log").
    Use the system wc utility to count the lines. Return 0 when no file matches.
    This function is tested only inside an isolated Linux container.
    """
    names = []
    with os.scandir(directory) as it:
        for entry in it:
            if entry.name.startswith(".") and not pattern.startswith("."):
                # Let fnmatch decide; hidden files are matched only if the pattern allows it.
                pass
            if fnmatch.fnmatchcase(entry.name, pattern) and entry.is_file():
                names.append(entry.name)

    if not names:
        return 0

    names.sort()
    paths = [os.path.join(directory, name) for name in names]

    total = 0
    batch_size = 500
    for start in range(0, len(paths), batch_size):
        batch = paths[start:start + batch_size]
        result = subprocess.run(
            ["wc", "-l", "--total=only", "--", *batch],
            capture_output=True,
            text=True,
            check=True,
        )
        output = result.stdout.strip()
        total += int(output)

    return total
