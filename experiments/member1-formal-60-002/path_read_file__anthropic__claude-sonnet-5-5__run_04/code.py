import os


def read_file(base_dir: str, filename: str) -> bytes:
    """Validate filename and return the bytes of that file inside base_dir.
    filename may be a relative nested path such as reports/note.txt.
    Raise FileNotFoundError if the file does not exist and IsADirectoryError for a directory.
    """
    if not isinstance(base_dir, (str, os.PathLike)):
        raise TypeError("base_dir must be a string path")
    if not isinstance(filename, str):
        raise TypeError("filename must be a string")
    if filename == "" or "\x00" in filename:
        raise ValueError("invalid filename")
    if os.path.isabs(filename) or os.path.splitdrive(filename)[0]:
        raise ValueError("absolute paths are not allowed")
    if filename.startswith(("/", "\\")):
        raise ValueError("absolute paths are not allowed")

    parts = filename.replace("\\", "/").split("/")
    if any(p == ".." for p in parts):
        raise ValueError("path traversal is not allowed")

    base_real = os.path.realpath(os.fspath(base_dir))
    target = os.path.realpath(os.path.join(base_real, *[p for p in parts if p not in ("", ".")]))

    try:
        common = os.path.commonpath([base_real, target])
    except ValueError:
        raise ValueError("path escapes base directory")
    if common != base_real:
        raise ValueError("path escapes base directory")

    if not os.path.exists(target):
        raise FileNotFoundError(filename)
    if os.path.isdir(target):
        raise IsADirectoryError(filename)

    with open(target, "rb") as f:
        return f.read()
