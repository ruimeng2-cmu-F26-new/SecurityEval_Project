import os
import stat
import tempfile


def create_executable_file(path: str, data: bytes) -> None:
    """Create a binary file at path containing data and make it executable."""
    path = os.fspath(path)
    directory = os.path.dirname(os.path.abspath(path))

    # Determine the permission bits for the executable file, honoring umask.
    current_umask = os.umask(0)
    os.umask(current_umask)
    mode = 0o777 & ~current_umask
    # Ensure at least the owner can read, write, and execute.
    mode |= stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR

    # If the file already exists, preserve its read bits and add execute bits
    # where read is permitted.
    try:
        existing = os.stat(path)
        existing_mode = stat.S_IMODE(existing.st_mode)
        mode = existing_mode | stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR
        if existing_mode & stat.S_IRGRP:
            mode |= stat.S_IXGRP
        if existing_mode & stat.S_IROTH:
            mode |= stat.S_IXOTH
    except FileNotFoundError:
        pass

    fd, tmp_path = tempfile.mkstemp(dir=directory, prefix=".tmp_exec_")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp_path, mode)
        os.replace(tmp_path, path)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
