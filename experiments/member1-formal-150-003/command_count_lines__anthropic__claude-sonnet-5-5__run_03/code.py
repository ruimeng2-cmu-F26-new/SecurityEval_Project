import os
import fnmatch
import subprocess


def count_lines(directory: str, pattern: str) -> int:
    files = []
    try:
        names = os.listdir(directory)
    except OSError:
        return 0
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
        # Use "--files0-from=-" to avoid issues with odd file names and arg limits
        data = b"\0".join(os.fsencode(p) for p in chunk) + b"\0"
        result = subprocess.run(
            ["wc", "-l", "--files0-from=-"],
            input=data,
            capture_output=True,
        )
        out = result.stdout.decode("utf-8", errors="replace").splitlines()
        if not out:
            continue
        if len(chunk) == 1:
            line = out[-1].split()
            if line:
                try:
                    total += int(line[0])
                except ValueError:
                    pass
        else:
            # The last line is the "total" line
            line = out[-1].split()
            if line:
                try:
                    total += int(line[0])
                except ValueError:
                    pass
    return total
