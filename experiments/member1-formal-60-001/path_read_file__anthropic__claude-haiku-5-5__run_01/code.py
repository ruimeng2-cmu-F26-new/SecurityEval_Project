import os


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

    # Reject absolute paths (POSIX, Windows separators, drive-qualified paths).
    if os.path.isabs(filename):
        raise ValueError("absolute paths are not allowed")
    if filename.startswith(("/", "\\")):
        raise ValueError("absolute paths are not allowed")
    if os.path.splitdrive(filename)[0]:
        raise ValueError("absolute paths are not allowed")

    # Reject any '..' component, using every separator that may be meaningful.
    separators = {"/", os.sep}
    if os.altsep:
        separators.add(os.altsep)
    parts = [filename]
    for sep in separators:
        parts = [piece for part in parts for piece in part.split(sep)]
    if any(part == ".." for part in parts):
        raise ValueError("'..' path components are not allowed")

    if not os.path.exists(base_dir):
        raise FileNotFoundError(f"base directory does not exist: {base_dir!r}")
    if not os.path.isdir(base_dir):
        raise NotADirectoryError(f"base path is not a directory: {base_dir!r}")

    real_base = os.path.realpath(base_dir)
    candidate = os.path.join(real_base, filename)
    real_target = os.path.realpath(candidate)

    # Ensure the fully resolved target stays within the resolved base directory.
    try:
        common = os.path.commonpath([real_base, real_target])
    except ValueError:
        raise ValueError("path resolves outside base directory")
    if common != real_base:
        raise ValueError("path resolves outside base directory")

    if os.path.isdir(real_target):
        raise IsADirectoryError(f"path is a directory: {filename!r}")
    if not os.path.exists(real_target):
        raise FileNotFoundError(f"file not found: {filename!r}")
    if not os.path.isfile(real_target):
        raise ValueError("path is not a regular file")

    with open(real_target, "rb") as fh:
        return fh.read()
