import os


_MAX_FILENAME_LENGTH = 255


def _sanitize_filename(filename: str) -> str:
    if not isinstance(filename, str):
        raise TypeError("filename must be a string")

    # Normalize client-supplied separators and keep only the final path component.
    name = filename.replace("\\", "/").split("/")[-1].strip()

    if not name or name in (".", ".."):
        raise ValueError("invalid filename")
    if name.startswith("."):
        raise ValueError("hidden filenames are not allowed")
    if "\x00" in name or any(ord(ch) < 32 or ord(ch) == 127 for ch in name):
        raise ValueError("filename contains control characters")
    if len(name.encode("utf-8", errors="strict")) > _MAX_FILENAME_LENGTH:
        raise ValueError("filename is too long")
    if os.path.splitext(name)[1].lower() != ".pdf":
        raise ValueError("filename must have a .pdf extension")

    return name


def save_pdf_upload(upload_dir: str, filename: str, data: bytes) -> str:
    """Save an uploaded PDF document: write data to a file in the existing directory
    upload_dir under the client-supplied filename, and return the path of the saved file.
    """
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError("data must be bytes-like")
    data = bytes(data)

    if not os.path.isdir(upload_dir):
        raise NotADirectoryError(f"upload directory does not exist: {upload_dir!r}")

    if not data.startswith(b"%PDF-"):
        raise ValueError("data does not appear to be a PDF document")

    safe_name = _sanitize_filename(filename)
    path = os.path.join(upload_dir, safe_name)

    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)

    fd = os.open(path, flags, 0o644)
    try:
        with os.fdopen(fd, "wb") as f:
            fd = -1
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
    finally:
        if fd != -1:
            os.close(fd)

    return path
