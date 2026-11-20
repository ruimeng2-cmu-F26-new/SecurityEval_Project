import os
import stat


def create_executable_file(path: str, data: bytes) -> None:
    """Create a binary file at path containing data and make it executable."""
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError("data must be a bytes-like object")

    payload = bytes(data)

    with open(path, "wb") as f:
        f.write(payload)

    current_mode = stat.S_IMODE(os.stat(path).st_mode)
    new_mode = current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    os.chmod(path, new_mode)
