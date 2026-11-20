import os
import fnmatch
import subprocess


def count_lines(directory: str, pattern: str) -> int:
    try:
        names = os.listdir(directory)
    except OSError:
        return 0

    files = []
    for name in sorted(names):
        if not fnmatch.fnmatchcase(name, pattern):
            continue
        path = os.path.join(directory, name)
        if os.path.isfile(path):
            files.append(path)

    if not files:
        return 0

    total = 0
    chunk_size = 500
    for i in range(0, len(files), chunk_size):
        chunk = files[i:i + chunk_size]
        # Use --files0-from=- to avoid argument/option parsing issues
        data = b"\0".join(os.fsencode(p) for p in chunk) + b"\0"
        result = subprocess.run(
            ["wc", "-l", "--files0-from=-"],
            input=data,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        lines = result.stdout.decode("utf-8", errors="replace").splitlines()
        if not lines:
            continue
        if len(chunk) == 1:
            parts = lines[0].split()
            if parts and parts[0].isdigit():
                total += int(parts[0])
        else:
            for line in reversed(lines):
                parts = line.split()
                if len(parts) >= 2 and parts[-1] == "total" and parts[0].isdigit():
                    total += int(parts[0])
                    break
    return total
