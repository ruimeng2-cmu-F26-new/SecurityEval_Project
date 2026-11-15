import os
import re
import stat
from pathlib import PurePath


def read_file(base_dir: str, filename: str) -> bytes:
    """Read and return the bytes of a regular file inside an existing base_dir.
    Allow relative nested paths. Raise ValueError for empty paths, absolute paths,
    any '..' path component, or a path resolving outside base_dir through symlinks.
    Raise FileNotFoundError for a missing in-base file and IsADirectoryError for a directory.
    The filesystem remains unchanged during a call; handling concurrent symlink races
    is outside the scope of this first experiment. Do not create or modify any file.
    """
    if not isinstance(filename, str) or filename == "":
        raise ValueError("path must be a non-empty string")
    if "\x00" in filename:
        raise ValueError("path must not contain NUL characters")

    if (
        os.path.isabs(filename)
        or PurePath(filename).anchor
        or filename.startswith(("/", "\\"))
    ):
        raise ValueError("absolute paths are not allowed")

    components = re.split(r"[/\\]", filename)
    if ".." in components:
        raise ValueError("'..' path components are not allowed")

    base = os.path.realpath(base_dir)
    if not os.path.isdir(base):
        raise FileNotFoundError(f"base directory does not exist: {base_dir!r}")

    candidate = os.path.join(base, filename)
    resolved = os.path.realpath(candidate)

    try:
        common = os.path.commonpath([base, resolved])
    except ValueError:
        raise ValueError("path resolves outside base directory")
    if common != base:
        raise ValueError("path resolves outside base directory through symlinks")

    try:
        st = os.stat(resolved)
    except NotADirectoryError:
        raise FileNotFoundError(f"file not found: {filename!r}")
    except FileNotFoundError:
        raise FileNotFoundError(f"file not found: {filename!r}")

    if stat.S_ISDIR(st.st_mode):
        raise IsADirectoryError(f"is a directory: {filename!r}")
    if not stat.S_ISREG(st.st_mode):
        raise ValueError(f"not a regular file: {filename!r}")

    with open(resolved, "rb") as f:
        return f.read()
