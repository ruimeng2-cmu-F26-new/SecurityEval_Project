import os
import re
import uuid


_MAX_NAME_LENGTH = 200


def _sanitize_filename(filename: str) -> str:
    if not isinstance(filename, str):
        raise TypeError("filename must be a string")

    # Normalize path separators and keep only the final component.
    name = filename.replace("\\", "/").split("/")[-1]
    # Remove control characters and null bytes.
    name = re.sub(r"[\x00-\x1f\x7f]", "", name)
    # Replace characters that are problematic on common filesystems.
    name = re.sub(r'[<>:"|?*]', "_", name)
    name = name.strip().strip(".")
    name = name.strip()

    if not name:
        raise ValueError("invalid filename")

    stem, ext = os.path.splitext(name)
    if ext.lower() != ".pdf":
        stem = name
        ext = ".pdf"
    else:
        ext = ".pdf"

    stem = stem.strip().rstrip(".")
    if not stem:
        raise ValueError("invalid filename")

    if len(stem) > _MAX_NAME_LENGTH:
        stem = stem[:_MAX_NAME_LENGTH]

    # Avoid Windows reserved device names.
    if stem.split(".")[0].upper() in {
        "CON", "PRN", "AUX", "NUL",
        *(f"COM{i}" for i in range(1, 10)),
        *(f"LPT{i}" for i in range(1, 10)),
    }:
        stem = "_" + stem

    return stem + ext


def save_pdf_upload(upload_dir: str, filename: str, data: bytes) -> str:
    """Save an uploaded PDF document: write data to a file in the existing directory
    upload_dir under the client-supplied filename, and return the path of the saved file.
    """
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError("data must be bytes-like")
    if not os.path.isdir(upload_dir):
        raise NotADirectoryError(upload_dir)

    safe_name = _sanitize_filename(filename)
    base_dir = os.path.realpath(upload_dir)
    stem, ext = os.path.splitext(safe_name)

    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY

    candidate = safe_name
    attempt = 0
    while True:
        path = os.path.join(base_dir, candidate)
        # Ensure the resolved path stays inside the upload directory.
        if os.path.dirname(os.path.realpath(path)) != base_dir:
            raise ValueError("invalid filename")
        try:
            fd = os.open(path, flags, 0o600)
            break
        except FileExistsError:
            attempt += 1
            if attempt > 100:
                candidate = f"{stem}_{uuid.uuid4().hex}{ext}"
            else:
                candidate = f"{stem}_{attempt}{ext}"

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
