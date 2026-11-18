import errno
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

    parts = [p for p in re.split(r"[\\/]+", filename) if p not in ("", ".")]
    if any(p == ".." for p in parts):
        raise ValueError("filename must not contain '..' components")

    base_real = os.path.realpath(base_dir)
    target = os.path.realpath(os.path.join(base_real, *parts)) if parts else base_real

    try:
        inside = os.path.commonpath([base_real, target]) == base_real
    except ValueError:
        inside = False
    if not inside:
        raise ValueError("filename resolves outside base_dir")

    if os.path.isdir(target):
        raise IsADirectoryError(errno.EISDIR, os.strerror(errno.EISDIR), filename)
    if not os.path.exists(target):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), filename)

    with open(target, "rb") as f:
        return f.read()
