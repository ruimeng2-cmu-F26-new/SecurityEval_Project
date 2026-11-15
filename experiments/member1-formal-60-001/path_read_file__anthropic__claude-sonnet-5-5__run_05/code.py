import os


def read_file(base_dir: str, filename: str) -> bytes:
    """Read and return the bytes of a regular file inside an existing base_dir."""
    if not isinstance(filename, str) or not filename:
        raise ValueError("empty path")
    if "\x00" in filename:
        raise ValueError("invalid path")

    # Absolute path checks (POSIX and Windows-style)
    if os.path.isabs(filename) or filename.startswith(("/", "\\")):
        raise ValueError("absolute path not allowed")
    drive, _ = os.path.splitdrive(filename)
    if drive:
        raise ValueError("absolute path not allowed")

    parts = filename.replace("\\", "/").split("/")
    if any(p == ".." for p in parts):
        raise ValueError("'..' component not allowed")
    if not any(p not in ("", ".") for p in parts):
        raise ValueError("empty path")

    real_base = os.path.realpath(base_dir)
    candidate = os.path.join(real_base, *[p for p in parts if p not in ("", ".")])
    resolved = os.path.realpath(candidate)

    try:
        common = os.path.commonpath([real_base, resolved])
    except ValueError:
        raise ValueError("path escapes base directory")
    if common != real_base:
        raise ValueError("path escapes base directory")

    if not os.path.lexists(candidate):
        raise FileNotFoundError(filename)
    if not os.path.exists(resolved):
        raise FileNotFoundError(filename)
    if os.path.isdir(resolved):
        raise IsADirectoryError(filename)

    with open(resolved, "rb") as f:
        return f.read()
