import os
import stat
import tempfile


def create_executable_file(path: str, data: bytes) -> None:
    """Create a binary file at path containing data and make it executable."""
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError("data must be bytes-like")

    payload = bytes(data)
    target = os.path.abspath(os.fspath(path))
    directory = os.path.dirname(target)

    fd, tmp_path = tempfile.mkstemp(dir=directory, prefix=".", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())

        mode = stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH
        os.chmod(tmp_path, mode)
        os.replace(tmp_path, target)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
