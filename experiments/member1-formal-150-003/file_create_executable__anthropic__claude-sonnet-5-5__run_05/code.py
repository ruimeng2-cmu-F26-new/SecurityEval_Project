import os
import stat
import tempfile


def create_executable_file(path: str, data: bytes) -> None:
    """Create a binary file at path containing data and make it executable."""
    path = os.fspath(path)
    directory = os.path.dirname(os.path.abspath(path))

    # Determine the current umask without permanently altering it.
    current_umask = os.umask(0)
    os.umask(current_umask)

    mode = 0o777 & ~current_umask
    # Ensure at least owner execute/read/write for the resulting file.
    mode |= stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR

    fd, tmp_path = tempfile.mkstemp(prefix=".tmp-", dir=directory)
    try:
        try:
            view = memoryview(data)
            while view:
                written = os.write(fd, view)
                view = view[written:]
            os.fsync(fd)
        finally:
            os.close(fd)
        os.chmod(tmp_path, mode)
        os.replace(tmp_path, path)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass
        raise
