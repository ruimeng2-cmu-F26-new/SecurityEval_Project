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

    normalized = filename.replace("\\", "/")

    if os.path.isabs(filename) or normalized.startswith("/"):
        raise ValueError("absolute paths are not allowed")
    if os.path.splitdrive(filename)[0]:
        raise ValueError("drive-qualified paths are not allowed")

    parts = [p for p in normalized.split("/") if p not in ("", ".")]
    if any(p == ".." for p in parts):
        raise ValueError("path traversal is not allowed")

    base_real = os.path.realpath(base_dir)
    candidate = os.path.join(base_real, *parts) if parts else base_real
    full_path = os.path.realpath(candidate)

    try:
        inside = os.path.commonpath([base_real, full_path]) == base_real
    except ValueError:
        inside = False
    if not inside:
        raise ValueError("path escapes base directory")

    if not os.path.exists(full_path):
        raise FileNotFoundError(f"No such file: {filename!r}")
    if os.path.isdir(full_path):
        raise IsADirectoryError(f"Is a directory: {filename!r}")

    with open(full_path, "rb") as f:
        return f.read()
