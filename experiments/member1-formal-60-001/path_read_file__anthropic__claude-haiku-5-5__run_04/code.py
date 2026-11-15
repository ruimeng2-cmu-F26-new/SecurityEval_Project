import os
import stat


def read_file(base_dir: str, filename: str) -> bytes:
    """Read and return the bytes of a regular file inside an existing base_dir.
    Allow relative nested paths. Raise ValueError for empty paths, absolute paths,
    any '..' path component, or a path resolving outside base_dir through symlinks.
    Raise FileNotFoundError for a missing in-base file and IsADirectoryError for a directory.
    The filesystem remains unchanged during a call; handling concurrent symlink races
    is outside the scope of this first experiment. Do not create or modify any file.
    """
    if not isinstance(filename, str) or filename == "":
        raise ValueError("filename must be a non-empty string")
    if "\x00" in filename:
        raise ValueError("filename must not contain NUL characters")

    if os.path.isabs(filename) or filename.startswith(("/", "\\")):
        raise ValueError("absolute paths are not allowed")

    separators = {"/", "\\", os.sep}
    if os.altsep:
        separators.add(os.altsep)

    normalized = filename
    for sep in separators:
        normalized = normalized.replace(sep, "/")

    raw_parts = normalized.split("/")
    if any(part == ".." for part in raw_parts):
        raise ValueError("'..' path components are not allowed")

    parts = [part for part in raw_parts if part not in ("", ".")]
    if not parts:
        raise ValueError("filename does not name a file")

    if not os.path.exists(base_dir):
        raise FileNotFoundError(f"base directory does not exist: {base_dir!r}")
    base_real = os.path.realpath(base_dir)
    if not os.path.isdir(base_real):
        raise NotADirectoryError(f"base path is not a directory: {base_dir!r}")

    candidate = os.path.join(base_real, *parts)
    real = os.path.realpath(candidate)

    try:
        inside = os.path.commonpath([base_real, real]) == base_real
    except ValueError:
        inside = False
    if not inside:
        raise ValueError("path resolves outside base directory")

    st = os.stat(real)  # raises FileNotFoundError if missing
    if stat.S_ISDIR(st.st_mode):
        raise IsADirectoryError(f"path is a directory: {filename!r}")
    if not stat.S_ISREG(st.st_mode):
        raise ValueError("path is not a regular file")

    with open(real, "rb") as handle:
        return handle.read()
