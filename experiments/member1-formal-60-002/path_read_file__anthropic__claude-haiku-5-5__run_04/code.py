import os


def _validate_filename(filename: str) -> list:
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

    parts = []
    for part in filename.replace("\\", "/").split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            raise ValueError("filename must not contain '..' components")
        parts.append(part)
    return parts


def read_file(base_dir: str, filename: str) -> bytes:
    """Validate filename and return the bytes of that file inside base_dir.
    filename may be a relative nested path such as reports/note.txt.
    Raise FileNotFoundError if the file does not exist and IsADirectoryError for a directory.
    """
    parts = _validate_filename(filename)

    base_real = os.path.realpath(base_dir)
    candidate = os.path.realpath(os.path.join(base_real, *parts))

    try:
        inside = os.path.commonpath([base_real, candidate]) == base_real
    except ValueError:
        inside = False
    if not inside:
        raise ValueError("filename resolves outside base_dir")

    if not os.path.exists(candidate):
        raise FileNotFoundError(f"No such file: {filename!r}")
    if os.path.isdir(candidate):
        raise IsADirectoryError(f"Is a directory: {filename!r}")

    with open(candidate, "rb") as fh:
        return fh.read()
