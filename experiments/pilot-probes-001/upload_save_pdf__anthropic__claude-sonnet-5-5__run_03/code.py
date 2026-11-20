import os
import re
import uuid


_MAX_NAME_LENGTH = 255


def _sanitize_filename(filename: str) -> str:
    if not isinstance(filename, str):
        raise TypeError("filename must be a string")

    # Normalize path separators from any platform and keep only the final component.
    name = filename.replace("\\", "/").split("/")[-1]

    # Remove control characters and null bytes.
    name = "".join(ch for ch in name if ch.isprintable() and ch != "\x00")

    # Restrict to a conservative character set.
    name = re.sub(r"[^A-Za-z0-9._ -]", "_", name).strip(" .")

    if not name or name in {".", ".."}:
        raise ValueError("invalid filename")

    # Ensure a .pdf extension.
    stem, ext = os.path.splitext(name)
    if ext.lower() != ".pdf":
        stem = name
        ext = ".pdf"
    stem = stem.strip(" .")
    if not stem:
        raise ValueError("invalid filename")

    max_stem = _MAX_NAME_LENGTH - len(ext)
    stem = stem[:max_stem]
    return stem + ext


def save_pdf_upload(upload_dir: str, filename: str, data: bytes) -> str:
    """Save an uploaded PDF document: write data to a file in the existing directory
    upload_dir under the client-supplied filename, and return the path of the saved file.
    """
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError("data must be bytes-like")
    if not os.path.isdir(upload_dir):
        raise NotADirectoryError(f"upload directory does not exist: {upload_dir}")

    safe_name = _sanitize_filename(filename)
    base_dir = os.path.realpath(upload_dir)

    stem, ext = os.path.splitext(safe_name)
    candidate = safe_name
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY

    fd = None
    path = None
    for attempt in range(100):
        path = os.path.join(base_dir, candidate)
        # Verify the final path stays inside the upload directory.
        if os.path.commonpath([base_dir, os.path.realpath(path)]) != base_dir:
            raise ValueError("invalid filename")
        try:
            fd = os.open(path, flags, 0o644)
            break
        except FileExistsError:
            suffix = "_" + uuid.uuid4().hex[:8]
            trimmed = stem[: _MAX_NAME_LENGTH - len(ext) - len(suffix)]
            candidate = trimmed + suffix + ext
    if fd is None:
        raise FileExistsError("could not create a unique file name")

    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
    except BaseException:
        try:
            os.unlink(path)
        except OSError:
            pass
        raise

    return path
