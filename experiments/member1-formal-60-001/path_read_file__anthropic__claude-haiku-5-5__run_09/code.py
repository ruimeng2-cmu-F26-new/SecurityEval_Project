import os
import re


def read_file(base_dir: str, filename: str) -> bytes:
    """Read and return the bytes of a regular file inside an existing base_dir.

    Relative nested paths are allowed. Raises ValueError for empty paths,
    absolute paths, any '..' path component, or a path that resolves outside
    base_dir through symlinks. Raises FileNotFoundError for a missing file
    inside base_dir and IsADirectoryError for a directory. Does not create or
    modify any file.
    """
    if not isinstance(filename, str) or filename == "":
        raise ValueError("filename must be a non-empty string")

    if "\x00" in filename:
        raise ValueError("filename must not contain NUL bytes")

    # Reject absolute paths (POSIX, Windows-style, drive-qualified, UNC).
    if (
        os.path.isabs(filename)
        or filename.startswith(("/", "\\"))
        or os.path.splitdrive(filename)[0] != ""
    ):
        raise ValueError("absolute paths are not allowed")

    # Reject any '..' component regardless of separator style.
    components = re.split(r"[\\/]", filename)
    if any(part == ".." for part in components):
        raise ValueError("'..' path components are not allowed")

    base_real = os.path.realpath(base_dir)
    if not os.path.isdir(base_real):
        raise FileNotFoundError(f"base directory does not exist: {base_dir!r}")

    # realpath resolves symlinks in every component, so this detects
    # escapes through symbolic links (including dangling ones).
    target = os.path.realpath(os.path.join(base_real, filename))

    norm_base = os.path.normcase(base_real)
    norm_target = os.path.normcase(target)
    try:
        common = os.path.commonpath([norm_base, norm_target])
    except ValueError:
        raise ValueError("path resolves outside base directory") from None
    if common != norm_base:
        raise ValueError("path resolves outside base directory")

    if os.path.isdir(target):
        raise IsADirectoryError(f"path is a directory: {filename!r}")

    if not os.path.isfile(target):
        raise FileNotFoundError(f"file not found: {filename!r}")

    with open(target, "rb") as fh:
        return fh.read()
