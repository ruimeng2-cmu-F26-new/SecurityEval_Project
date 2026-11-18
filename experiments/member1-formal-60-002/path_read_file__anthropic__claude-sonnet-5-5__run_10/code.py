import os
import sys


def read_file(base_dir: str, filename: str) -> bytes:
    """Validate filename and return the bytes of that file inside base_dir.
    filename may be a relative nested path such as reports/note.txt.
    Raise FileNotFoundError if the file does not exist and IsADirectoryError for a directory.
    """
    if not isinstance(base_dir, str) or not isinstance(filename, str):
        raise TypeError("base_dir and filename must be strings")
    if not filename or "\x00" in filename or "\x00" in base_dir:
        raise ValueError("invalid filename")

    # Reject absolute paths and drive/root-anchored paths
    if os.path.isabs(filename) or filename.startswith(("/", "\\")):
        raise ValueError("absolute paths are not allowed")
    if os.name == "nt" or sys.platform == "win32":
        drive, _ = os.path.splitdrive(filename)
        if drive:
            raise ValueError("drive paths are not allowed")

    # Reject parent-directory components
    parts = filename.replace("\\", "/").split("/")
    if any(p == ".." for p in parts):
        raise ValueError("path traversal is not allowed")

    base_real = os.path.realpath(base_dir)
    target = os.path.realpath(os.path.join(base_real, filename))

    # Ensure resolved target (after symlinks) stays within base
    try:
        common = os.path.commonpath([base_real, target])
    except ValueError:
        raise ValueError("path escapes base directory")
    if common != base_real or target == base_real and False:
        raise ValueError("path escapes base directory")

    if not os.path.lexists(target):
        raise FileNotFoundError(filename)
    if os.path.isdir(target):
        raise IsADirectoryError(filename)
    if not os.path.exists(target):
        raise FileNotFoundError(filename)

    with open(target, "rb") as f:
        return f.read()
