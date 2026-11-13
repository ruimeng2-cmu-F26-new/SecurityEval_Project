import os


def read_file(base_dir: str, filename: str) -> bytes:
    """Read and return the bytes of a regular file inside an existing base_dir."""
    if not isinstance(filename, str) or not isinstance(base_dir, str):
        raise ValueError("base_dir and filename must be strings")
    if filename == "" or "\x00" in filename:
        raise ValueError("invalid filename")

    # Normalize separators for component checking
    parts = [filename]
    if os.sep != "/":
        parts = filename.split(os.sep)
        parts = [p for part in parts for p in part.split("/")]
    else:
        parts = filename.split("/")
    if any(p == ".." for p in parts):
        raise ValueError("'..' components are not allowed")

    if os.path.isabs(filename) or filename.startswith(("/", os.sep)):
        raise ValueError("absolute paths are not allowed")
    if os.name == "nt":
        drive, _ = os.path.splitdrive(filename)
        if drive:
            raise ValueError("absolute paths are not allowed")

    if all(p in ("", ".") for p in parts):
        raise ValueError("empty path")

    base_real = os.path.realpath(base_dir)
    candidate = os.path.join(base_dir, filename)
    real = os.path.realpath(candidate)

    try:
        common = os.path.commonpath([base_real, real])
    except ValueError:
        raise ValueError("path resolves outside base_dir")
    if common != base_real:
        raise ValueError("path resolves outside base_dir")

    if not os.path.lexists(candidate):
        raise FileNotFoundError(filename)
    if not os.path.exists(real):
        # dangling symlink inside base
        raise FileNotFoundError(filename)
    if os.path.isdir(real):
        raise IsADirectoryError(filename)
    if not os.path.isfile(real):
        raise ValueError("not a regular file")

    with open(real, "rb") as f:
        return f.read()
