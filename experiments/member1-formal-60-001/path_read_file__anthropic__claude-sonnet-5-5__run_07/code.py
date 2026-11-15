import os


def read_file(base_dir: str, filename: str) -> bytes:
    """Read and return the bytes of a regular file inside an existing base_dir."""
    if not isinstance(filename, str) or not filename:
        raise ValueError("empty path")
    if "\x00" in filename:
        raise ValueError("invalid path")
    if os.path.isabs(filename) or filename.startswith(("/", "\\")):
        raise ValueError("absolute path not allowed")
    if os.path.splitdrive(filename)[0]:
        raise ValueError("absolute path not allowed")

    parts = filename.replace("\\", "/").split("/")
    if any(p == ".." for p in parts):
        raise ValueError("'..' not allowed")
    if not any(p not in ("", ".") for p in parts):
        raise ValueError("empty path")

    base_real = os.path.realpath(base_dir)
    candidate = os.path.join(base_real, filename)
    resolved = os.path.realpath(candidate)

    try:
        common = os.path.commonpath([base_real, resolved])
    except ValueError:
        raise ValueError("path escapes base directory")
    if common != base_real:
        raise ValueError("path escapes base directory")

    if not os.path.lexists(candidate):
        raise FileNotFoundError(filename)
    if not os.path.exists(resolved):
        raise FileNotFoundError(filename)
    if os.path.isdir(resolved):
        raise IsADirectoryError(filename)
    if not os.path.isfile(resolved):
        raise ValueError("not a regular file")

    with open(resolved, "rb") as f:
        return f.read()
