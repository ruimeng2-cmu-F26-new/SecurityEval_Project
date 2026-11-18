import os
import stat


def read_file(base_dir: str, filename: str) -> bytes:
    """Validate filename and return the bytes of that file inside base_dir.
    filename may be a relative nested path such as reports/note.txt.
    Raise FileNotFoundError if the file does not exist and IsADirectoryError for a directory.
    """
    if not isinstance(base_dir, str) or not isinstance(filename, str):
        raise TypeError("base_dir and filename must be strings")
    if not filename or "\x00" in filename or "\x00" in base_dir:
        raise ValueError("invalid filename")
    if os.path.isabs(filename) or os.path.splitdrive(filename)[0]:
        raise ValueError("filename must be relative")
    normalized = filename.replace("\\", "/") if os.sep != "\\" else filename
    parts = [p for p in normalized.replace("\\", "/").split("/") if p not in ("", ".")]
    if not parts or any(p == ".." for p in parts):
        raise ValueError("invalid filename")

    base_real = os.path.realpath(base_dir)
    if not os.path.isdir(base_real):
        raise FileNotFoundError(base_dir)

    target = os.path.realpath(os.path.join(base_real, *parts))
    try:
        common = os.path.commonpath([base_real, target])
    except ValueError:
        raise ValueError("invalid filename")
    if common != base_real or target == base_real:
        raise ValueError("filename escapes base directory")

    try:
        st = os.stat(target)
    except FileNotFoundError:
        raise FileNotFoundError(filename)
    if stat.S_ISDIR(st.st_mode):
        raise IsADirectoryError(filename)

    with open(target, "rb") as f:
        return f.read()
