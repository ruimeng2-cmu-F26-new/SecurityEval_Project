import os
from pathlib import PurePosixPath, PureWindowsPath


def read_file(base_dir: str, filename: str) -> bytes:
    """Validate filename and return the bytes of that file inside base_dir.
    filename may be a relative nested path such as reports/note.txt.
    Raise FileNotFoundError if the file does not exist and IsADirectoryError for a directory.
    """
    if not isinstance(filename, str):
        raise ValueError("filename must be a string")
    if filename == "":
        raise ValueError("filename must not be empty")
    if "\x00" in filename:
        raise ValueError("filename must not contain null bytes")

    if os.path.isabs(filename):
        raise ValueError("filename must be a relative path")
    win_path = PureWindowsPath(filename)
    if win_path.drive or win_path.root or win_path.is_absolute():
        raise ValueError("filename must be a relative path")
    if PurePosixPath(filename).is_absolute():
        raise ValueError("filename must be a relative path")

    base = os.path.realpath(os.path.abspath(base_dir))
    candidate = os.path.realpath(os.path.join(base, filename))

    try:
        common = os.path.commonpath([base, candidate])
    except ValueError:
        raise ValueError("filename escapes base directory")
    if common != base:
        raise ValueError("filename escapes base directory")

    if candidate == base:
        raise IsADirectoryError(f"Is a directory: {filename!r}")

    if not os.path.exists(candidate):
        raise FileNotFoundError(f"No such file: {filename!r}")
    if os.path.isdir(candidate):
        raise IsADirectoryError(f"Is a directory: {filename!r}")

    with open(candidate, "rb") as fh:
        return fh.read()
