import os
import re


def read_file(base_dir: str, filename: str) -> bytes:
    """Validate filename and return the bytes of that file inside base_dir.
    filename may be a relative nested path such as reports/note.txt.
    Raise FileNotFoundError if the file does not exist and IsADirectoryError for a directory.
    """
    if not isinstance(filename, str):
        raise ValueError("filename must be a string")
    if not filename:
        raise ValueError("filename must not be empty")
    if "\x00" in filename:
        raise ValueError("filename must not contain null bytes")
    if os.path.isabs(filename) or filename.startswith(("/", "\\")):
        raise ValueError("filename must be a relative path")
    if os.path.splitdrive(filename)[0]:
        raise ValueError("filename must not contain a drive specifier")

    parts = re.split(r"[\\/]", filename)
    if any(part == ".." for part in parts):
        raise ValueError("filename must not contain parent directory references")

    base_real = os.path.realpath(base_dir)
    candidate = os.path.realpath(os.path.join(base_real, *parts))

    try:
        common = os.path.commonpath([base_real, candidate])
    except ValueError:
        raise ValueError("filename resolves outside base directory")
    if common != base_real or candidate == base_real:
        if candidate == base_real:
            raise IsADirectoryError(f"Is a directory: {filename!r}")
        raise ValueError("filename resolves outside base directory")

    if os.path.isdir(candidate):
        raise IsADirectoryError(f"Is a directory: {filename!r}")
    if not os.path.exists(candidate):
        raise FileNotFoundError(f"No such file: {filename!r}")

    with open(candidate, "rb") as f:
        return f.read()
