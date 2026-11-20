import os
import stat


def create_executable_file(path: str, data: bytes) -> None:
    """Create a binary file at path containing data and make it executable."""
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError("data must be bytes-like")

    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY

    fd = os.open(path, flags, 0o755)
    with os.fdopen(fd, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())

    mode = os.stat(path).st_mode
    exec_bits = stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    os.chmod(path, mode | exec_bits)
