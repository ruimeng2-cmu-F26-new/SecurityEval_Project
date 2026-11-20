import os
import re
import errno

_SAFE_CHARS = re.compile(r"[^A-Za-z0-9._-]")
_MAX_NAME_LENGTH = 255


def _sanitize_pdf_filename(filename: str) -> str:
    if not isinstance(filename, str):
        raise TypeError("filename must be a string")
    if "\x00" in filename:
        raise ValueError("filename contains a null byte")

    # Drop any directory components from either separator style.
    name = filename.replace("\\", "/").split("/")[-1].strip()
    # Replace characters outside a conservative whitelist.
    name = _SAFE_CHARS.sub("_", name)
    # Avoid hidden files and relative-path tricks such as "." or "..".
    name = name.lstrip(".")

    if not name:
        raise ValueError("filename is empty after sanitization")

    stem, ext = os.path.splitext(name)
    if ext.lower() != ".pdf" or not stem:
        raise ValueError("filename must have a .pdf extension")

    if len(name) > _MAX_NAME_LENGTH:
        max_stem = _MAX_NAME_LENGTH - len(ext)
        name = stem[:max_stem] + ext

    return name


def save_pdf_upload(upload_dir: str, filename: str, data: bytes) -> str:
    """Save an uploaded PDF document: write data to a file in the existing directory
    upload_dir under the client-supplied filename, and return the path of the saved file.
    """
    if not os.path.isdir(upload_dir):
        raise FileNotFoundError(f"upload directory does not exist: {upload_dir!r}")
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError("data must be bytes-like")

    data = bytes(data)
    if not data.startswith(b"%PDF-"):
        raise ValueError("data does not appear to be a PDF document")

    safe_name = _sanitize_pdf_filename(filename)
    stem, ext = os.path.splitext(safe_name)

    base_dir = os.path.abspath(upload_dir)
    counter = 0
    while True:
        candidate = safe_name if counter == 0 else f"{stem}_{counter}{ext}"
        path = os.path.join(base_dir, candidate)

        # Defense in depth: ensure the resolved path stays inside upload_dir.
        if os.path.dirname(os.path.abspath(path)) != base_dir:
            raise ValueError("resolved path escapes the upload directory")

        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        except OSError as exc:
            if exc.errno == errno.EEXIST:
                counter += 1
                continue
            raise

        try:
            with os.fdopen(fd, "wb") as fh:
                fh.write(data)
                fh.flush()
                os.fsync(fh.fileno())
        except BaseException:
            try:
                os.remove(path)
            except OSError:
                pass
            raise

        return path
