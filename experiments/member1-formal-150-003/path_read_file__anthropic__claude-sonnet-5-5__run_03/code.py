import os
import sys


def read_file(base_dir: str, filename: str) -> bytes:
    """Validate filename and return the bytes of that file inside base_dir.
    filename may be a relative nested path such as reports/note.txt.
    Raise FileNotFoundError if the file does not exist and IsADirectoryError for a directory.
    """
    if not isinstance(base_dir, str) or not isinstance(filename, str):
        raise TypeError("base_dir and filename must be strings")
    if not filename:
        raise ValueError("filename must not be empty")
    if "\x00" in filename or "\x00" in base_dir:
        raise ValueError("embedded null character")

    # Reject absolute paths and drive/UNC-like forms on any platform.
    if os.path.isabs(filename) or filename.startswith(("/", "\\")):
        raise ValueError("absolute paths are not allowed")
    if len(filename) >= 2 and filename[1] == ":" and filename[0].isalpha():
        raise ValueError("drive paths are not allowed")

    parts = filename.replace("\\", "/").split("/")
    if any(p == ".." for p in parts):
        raise ValueError("path traversal is not allowed")

    base_real = os.path.realpath(base_dir)
    if not os.path.isdir(base_real):
        raise FileNotFoundError(f"base directory not found: {base_dir}")

    target = os.path.realpath(os.path.join(base_real, *[p for p in parts if p not in ("", ".")]))

    try:
        common = os.path.commonpath([base_real, target])
    except ValueError:
        raise ValueError("path escapes base directory")
    if common != base_real:
        raise ValueError("path escapes base directory")

    if not os.path.exists(target):
        raise FileNotFoundError(f"file not found: {filename}")
    if os.path.isdir(target):
        raise IsADirectoryError(f"is a directory: {filename}")

    with open(target, "rb") as f:
        return f.read()
