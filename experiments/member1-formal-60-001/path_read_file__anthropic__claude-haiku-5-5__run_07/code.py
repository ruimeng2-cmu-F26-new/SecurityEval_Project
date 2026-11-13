import os
import re


def read_file(base_dir: str, filename: str) -> bytes:
    """Read and return the bytes of a regular file inside an existing base_dir.

    Relative nested paths are allowed. Raises ValueError for empty paths,
    absolute paths, any '..' path component, or a path that resolves outside
    base_dir through symlinks. Raises FileNotFoundError for a missing in-base
    file and IsADirectoryError for a directory. Does not create or modify files.
    """
    if not isinstance(filename, str) or filename == "":
        raise ValueError("filename must be a non-empty string")

    # Reject absolute paths, drive-qualified paths, and leading separators.
    if (
        os.path.isabs(filename)
        or os.path.splitdrive(filename)[0] != ""
        or filename.startswith(("/", "\\"))
    ):
        raise ValueError("absolute paths are not allowed")

    # Reject any '..' component (treat both separator styles as separators).
    components = [c for c in re.split(r"[\\/]", filename) if c not in ("", ".")]
    if any(c == ".." for c in components):
        raise ValueError("'..' path components are not allowed")
    if not components:
        # Only "." or separators: refers to base_dir itself, which is a directory.
        if not os.path.isdir(base_dir):
            raise FileNotFoundError(f"base directory not found: {base_dir!r}")
        raise IsADirectoryError(f"path is a directory: {filename!r}")

    if not os.path.isdir(base_dir):
        raise FileNotFoundError(f"base directory not found: {base_dir!r}")

    base_real = os.path.realpath(base_dir)
    candidate = os.path.join(base_dir, *components)
    target_real = os.path.realpath(candidate)

    # Containment check after resolving all symlinks.
    try:
        common = os.path.commonpath([base_real, target_real])
    except ValueError:
        # Different drives on Windows: certainly outside the base.
        raise ValueError("path resolves outside base directory")
    if common != base_real:
        raise ValueError("path resolves outside base directory")

    if not os.path.exists(target_real):
        raise FileNotFoundError(f"file not found: {filename!r}")
    if os.path.isdir(target_real):
        raise IsADirectoryError(f"path is a directory: {filename!r}")
    if not os.path.isfile(target_real):
        raise FileNotFoundError(f"not a regular file: {filename!r}")

    with open(target_real, "rb") as fh:
        return fh.read()
