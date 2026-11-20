import os
import stat


def create_executable_file(path: str, data: bytes) -> None:
    """Create a binary file at path containing data and make it executable."""
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY

    fd = os.open(path, flags, 0o755)
    try:
        view = memoryview(data)
        while view:
            written = os.write(fd, view)
            view = view[written:]

        if hasattr(os, "fchmod"):
            current = os.fstat(fd).st_mode
            # Grant execute permission wherever read permission is present.
            mode = stat.S_IMODE(current) | ((current & 0o444) >> 2)
            os.fchmod(fd, mode)
    finally:
        os.close(fd)
