import os
import stat


def create_executable_file(path: str, data: bytes) -> None:
    """Create a binary file at path containing data and make it executable."""
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError("data must be a bytes-like object")

    with open(path, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())

    current_mode = os.stat(path).st_mode
    exec_bits = stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    os.chmod(path, stat.S_IMODE(current_mode) | exec_bits)
