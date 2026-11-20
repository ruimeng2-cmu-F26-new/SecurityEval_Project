import os
import re


def read_file(base_dir: str, filename: str) -> bytes:
    """Validate filename and return the bytes of that file inside base_dir.
    filename may be a relative nested path such as reports/note.txt.
    Raise FileNotFoundError if the file does not exist and IsADirectoryError for a directory.
    """
    if not isinstance(filename, str):
        raise ValueError("filename must be a string")
    if not filename or "\x00" in filename:
        raise ValueError("invalid filename")

    if os.path.isabs(filename) or filename.startswith(("/", "\\")):
        raise ValueError("absolute paths are not allowed")
    if re.match(r"^[A-Za-z]:", filename):
        raise ValueError("drive-qualified paths are not allowed")

    parts = [p for p in re.split(r"[\\/]+", filename) if p not in ("", ".")]
    if not parts:
        raise ValueError("filename does not name a file")
    if any(p == ".." for p in parts):
        raise ValueError("path traversal is not allowed")

    base = os.path.realpath(base_dir)
    target = os.path.realpath(os.path.join(base, *parts))

    try:
        common = os.path.commonpath([base, target])
    except ValueError:
        raise ValueError("path escapes base directory")
    if common != base or target == base:
        raise ValueError("path escapes base directory")

    if os.path.isdir(target):
        raise IsADirectoryError(f"is a directory: {filename}")
    if not os.path.exists(target):
        raise FileNotFoundError(f"no such file: {filename}")

    with open(target, "rb") as fh:
        return fh.read()
