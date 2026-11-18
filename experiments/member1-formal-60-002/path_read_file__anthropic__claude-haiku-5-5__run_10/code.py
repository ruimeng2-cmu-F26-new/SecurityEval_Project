import os


def _validate_relative_parts(filename: str) -> list:
    if not isinstance(filename, str):
        raise ValueError("filename must be a string")
    if not filename:
        raise ValueError("filename must not be empty")
    if "\x00" in filename:
        raise ValueError("filename must not contain null bytes")
    if "\\" in filename:
        raise ValueError("filename must not contain backslashes")
    if filename.startswith("/") or os.path.isabs(filename):
        raise ValueError("filename must be a relative path")
    if len(filename) >= 2 and filename[1] == ":":
        raise ValueError("filename must not contain a drive specifier")

    parts = filename.split("/")
    for part in parts:
        if part == "":
            raise ValueError("filename must not contain empty path components")
        if part == "..":
            raise ValueError("filename must not contain '..' components")
        if part == ".":
            raise ValueError("filename must not contain '.' components")
    return parts


def read_file(base_dir: str, filename: str) -> bytes:
    """Validate filename and return the bytes of that file inside base_dir.
    filename may be a relative nested path such as reports/note.txt.
    Raise FileNotFoundError if the file does not exist and IsADirectoryError for a directory.
    """
    parts = _validate_relative_parts(filename)

    base_real = os.path.realpath(os.fspath(base_dir))
    candidate = os.path.join(base_real, *parts)
    target_real = os.path.realpath(candidate)

    try:
        inside = os.path.commonpath([base_real, target_real]) == base_real
    except ValueError:
        inside = False
    if not inside:
        raise PermissionError("filename resolves outside base_dir")

    if not os.path.exists(target_real):
        raise FileNotFoundError(f"No such file: {filename!r}")
    if os.path.isdir(target_real):
        raise IsADirectoryError(f"Is a directory: {filename!r}")

    with open(target_real, "rb") as fh:
        return fh.read()
