import os


def read_file(base_dir: str, filename: str) -> bytes:
    """Read and return the bytes of a regular file inside an existing base_dir."""
    if not isinstance(filename, str) or not filename:
        raise ValueError("empty path")
    if "\x00" in filename:
        raise ValueError("invalid path")

    normalized = filename.replace("\\", "/") if os.sep == "\\" else filename

    if os.path.isabs(filename) or normalized.startswith("/"):
        raise ValueError("absolute path not allowed")
    if os.path.splitdrive(filename)[0]:
        raise ValueError("absolute path not allowed")

    parts = normalized.split("/")
    if any(part == ".." for part in parts):
        raise ValueError("'..' component not allowed")
    if not any(part not in ("", ".") for part in parts):
        raise ValueError("empty path")

    base_real = os.path.realpath(base_dir)
    candidate = os.path.join(base_real, *[p for p in parts if p not in ("", ".")])
    resolved = os.path.realpath(candidate)

    try:
        common = os.path.commonpath([base_real, resolved])
    except ValueError:
        raise ValueError("path resolves outside base directory")
    if common != base_real:
        raise ValueError("path resolves outside base directory")

    if not os.path.lexists(candidate) or not os.path.exists(resolved):
        raise FileNotFoundError(filename)
    if os.path.isdir(resolved):
        raise IsADirectoryError(filename)
    if not os.path.isfile(resolved):
        raise ValueError("not a regular file")

    with open(resolved, "rb") as f:
        return f.read()
