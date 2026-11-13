import os
import stat


def read_file(base_dir: str, filename: str) -> bytes:
    if not isinstance(base_dir, str) or not isinstance(filename, str):
        raise ValueError("base_dir and filename must be strings")
    if filename == "":
        raise ValueError("filename must not be empty")
    if "\x00" in filename:
        raise ValueError("filename must not contain NUL characters")
    if os.path.isabs(filename) or filename.startswith(("/", "\\")):
        raise ValueError("absolute paths are not allowed")

    separators = {"/", os.sep}
    if os.altsep:
        separators.add(os.altsep)
    parts = [""]
    for ch in filename:
        if ch in separators:
            parts.append("")
        else:
            parts[-1] += ch
    components = [p for p in parts if p not in ("", ".")]
    if any(p == ".." for p in parts):
        raise ValueError("'..' path components are not allowed")
    if not components:
        raise ValueError("filename does not name a file")

    real_base = os.path.realpath(base_dir)
    if not os.path.isdir(real_base):
        raise FileNotFoundError(f"base directory does not exist: {base_dir!r}")

    candidate = os.path.join(real_base, *components)
    real_candidate = os.path.realpath(candidate)

    try:
        common = os.path.commonpath([real_base, real_candidate])
    except ValueError:
        common = None
    if common != real_base:
        raise ValueError("path resolves outside base directory")

    st = os.stat(real_candidate)  # raises FileNotFoundError if missing
    if stat.S_ISDIR(st.st_mode):
        raise IsADirectoryError(f"path is a directory: {filename!r}")
    if not stat.S_ISREG(st.st_mode):
        raise ValueError("path is not a regular file")

    with open(real_candidate, "rb") as f:
        return f.read()
