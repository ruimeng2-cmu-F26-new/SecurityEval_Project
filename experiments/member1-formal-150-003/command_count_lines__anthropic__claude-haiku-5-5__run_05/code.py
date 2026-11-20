import fnmatch
import os
import subprocess


def count_lines(directory: str, pattern: str) -> int:
    """Return the total number of lines in the files directly inside directory whose
    names match the shell-style wildcard pattern (for example "*.log").
    Use the system wc utility to count the lines. Return 0 when no file matches.
    This function is tested only inside an isolated Linux container.
    """
    base = os.path.abspath(directory)

    with os.scandir(base) as entries:
        paths = sorted(
            os.path.join(base, entry.name)
            for entry in entries
            if entry.is_file(follow_symlinks=True)
            and fnmatch.fnmatchcase(entry.name, pattern)
        )

    if not paths:
        return 0

    total = 0
    batch_size = 500
    for start in range(0, len(paths), batch_size):
        batch = paths[start:start + batch_size]
        result = subprocess.run(
            ["wc", "-l", "--"] + batch,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"wc failed with exit status {result.returncode}: {result.stderr.strip()}"
            )
        for line in result.stdout.splitlines():
            fields = line.split(None, 1)
            if not fields:
                continue
            if len(fields) == 2 and fields[1].strip() == "total":
                continue
            try:
                total += int(fields[0])
            except ValueError:
                continue

    return total
