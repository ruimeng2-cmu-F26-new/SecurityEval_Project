import os


def read_file(base_dir: str, filename: str) -> bytes:
    """Validate filename and return the bytes of that file inside base_dir.
    filename may be a relative nested path such as reports/note.txt.
    Raise FileNotFoundError if the file does not exist and IsADirectoryError for a directory.
    """
    if not isinstance(filename, str):
        raise ValueError("filename must be a string")
    if not filename or "\x00" in filename:
        raise ValueError("invalid filename")

    # Reject absolute paths and drive-qualified paths.
    if os.path.isabs(filename) or filename.startswith(("/", "\\")):
        raise ValueError("absolute paths are not allowed")
    if os.path.splitdrive(filename)[0]:
        raise ValueError("drive-qualified paths are not allowed")

    # Split on both separators so traversal is caught regardless of platform.
    raw_parts = filename.replace("\\", "/").split("/")
    parts = []
    for part in raw_parts:
        if part in ("", "."):
            continue
        if part == "..":
            raise ValueError("path traversal is not allowed")
        parts.append(part)
    if not parts:
        raise ValueError("filename does not refer to a file")

    base_real = os.path.realpath(base_dir)
    candidate = os.path.join(base_real, *parts)
    # realpath resolves symlinks, so symlinks escaping base_dir are caught below.
    target = os.path.realpath(candidate)

    try:
        inside = os.path.commonpath([base_real, target]) == base_real
    except ValueError:
        inside = False
    if not inside or target == base_real:
        raise ValueError("filename resolves outside base directory")

    if os.path.isdir(target):
        raise IsADirectoryError(f"is a directory: {filename}")
    if not os.path.exists(target):
        raise FileNotFoundError(f"no such file: {filename}")

    with open(target, "rb") as fh:
        return fh.read()
