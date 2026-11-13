import os


def read_file(base_dir: str, filename: str) -> bytes:
    """Read and return the bytes of a regular file inside an existing base_dir."""
    if not isinstance(filename, str) or not isinstance(base_dir, str):
        raise ValueError("base_dir and filename must be strings")
    if filename == "" or "\x00" in filename:
        raise ValueError("invalid filename")

    # Absolute path checks (POSIX and Windows styles)
    if os.path.isabs(filename) or filename.startswith(("/", "\\")):
        raise ValueError("absolute paths are not allowed")
    if len(filename) >= 2 and filename[1] == ":" and filename[0].isalpha():
        raise ValueError("absolute paths are not allowed")

    parts = filename.replace("\\", "/").split("/")
    if any(p == ".." for p in parts):
        raise ValueError("'..' components are not allowed")
    if all(p in ("", ".") for p in parts):
        raise ValueError("empty path")

    real_base = os.path.realpath(base_dir)
    candidate = os.path.join(real_base, *[p for p in parts if p not in ("", ".")])
    resolved = os.path.realpath(candidate)

    try:
        common = os.path.commonpath([real_base, resolved])
    except ValueError:
        raise ValueError("path resolves outside base directory")
    if common != real_base:
        raise ValueError("path resolves outside base directory")

    if not os.path.exists(resolved):
        raise FileNotFoundError(filename)
    if os.path.isdir(resolved):
        raise IsADirectoryError(filename)
    if not os.path.isfile(resolved):
        raise FileNotFoundError(filename)

    with open(resolved, "rb") as f:
        return f.read()
