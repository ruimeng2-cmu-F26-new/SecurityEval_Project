import os
import errno


def read_file(base_dir: str, filename: str) -> bytes:
    """Validate filename and return the bytes of that file inside base_dir.
    filename may be a relative nested path such as reports/note.txt.
    Raise FileNotFoundError if the file does not exist and IsADirectoryError for a directory.
    """
    if not isinstance(filename, str):
        raise TypeError("filename must be a string")
    if filename == "":
        raise ValueError("filename must not be empty")
    if "\x00" in filename:
        raise ValueError("filename must not contain null bytes")
    if os.path.isabs(filename) or filename.startswith(("/", "\\")):
        raise ValueError("filename must be a relative path")

    parts = [p for p in filename.replace("\\", "/").split("/") if p not in ("", ".")]
    if not parts:
        raise ValueError("filename does not name a file")
    if any(p == ".." for p in parts):
        raise ValueError("filename must not contain '..' components")
    if any(":" in p for p in parts) and os.name == "nt":
        raise ValueError("filename must not contain drive specifiers")

    base_real = os.path.realpath(base_dir)
    candidate = os.path.realpath(os.path.join(base_real, *parts))

    try:
        inside = os.path.commonpath([base_real, candidate]) == base_real
    except ValueError:
        inside = False
    if not inside or candidate == base_real:
        raise ValueError("filename resolves outside the base directory")

    if os.path.isdir(candidate):
        raise IsADirectoryError(errno.EISDIR, os.strerror(errno.EISDIR), filename)

    if not os.path.exists(candidate):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), filename)

    with open(candidate, "rb") as fh:
        return fh.read()
