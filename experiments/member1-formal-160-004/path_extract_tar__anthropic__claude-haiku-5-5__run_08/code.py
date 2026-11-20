import copy
import os
import tarfile


class UnsafeArchiveError(tarfile.TarError):
    """Raised when an archive entry would extract outside the destination."""


def _is_within(base: str, path: str) -> bool:
    try:
        return os.path.commonpath([base, path]) == base
    except ValueError:
        return False


def _check_member_static(member: tarfile.TarInfo, dest_real: str) -> None:
    name = member.name
    if not name or "\x00" in name:
        raise UnsafeArchiveError(f"invalid member name: {name!r}")
    if os.path.isabs(name) or os.path.splitdrive(name)[0] or name.startswith(("/", "\\")):
        raise UnsafeArchiveError(f"absolute member path not allowed: {name!r}")
    if member.isdev():
        raise UnsafeArchiveError(f"device entry not allowed: {name!r}")

    target = os.path.normpath(os.path.join(dest_real, name))
    if not _is_within(dest_real, target):
        raise UnsafeArchiveError(f"member escapes destination: {name!r}")

    if member.issym():
        link = member.linkname
        if not link or "\x00" in link or os.path.isabs(link) or os.path.splitdrive(link)[0]:
            raise UnsafeArchiveError(f"unsafe symlink target: {link!r}")
        resolved = os.path.realpath(os.path.join(os.path.dirname(target), link))
        if not _is_within(dest_real, resolved):
            raise UnsafeArchiveError(f"symlink escapes destination: {name!r} -> {link!r}")
    elif member.islnk():
        link = member.linkname
        if not link or "\x00" in link or os.path.isabs(link) or os.path.splitdrive(link)[0]:
            raise UnsafeArchiveError(f"unsafe hardlink target: {link!r}")
        source = os.path.normpath(os.path.join(dest_real, link))
        if not _is_within(dest_real, source):
            raise UnsafeArchiveError(f"hardlink escapes destination: {name!r} -> {link!r}")


def _prepare_parent(target: str, dest_real: str) -> None:
    """Ensure the parent directory of target resolves inside dest_real, then create it."""
    parent = os.path.dirname(target)

    probe = parent
    while not os.path.lexists(probe):
        next_probe = os.path.dirname(probe)
        if next_probe == probe:
            break
        probe = next_probe
    if not _is_within(dest_real, os.path.realpath(probe)):
        raise UnsafeArchiveError(f"path resolves outside destination: {target!r}")

    os.makedirs(parent, exist_ok=True)

    if not _is_within(dest_real, os.path.realpath(parent)):
        raise UnsafeArchiveError(f"path resolves outside destination: {target!r}")


def extract_tar(archive_path: str, dest_dir: str) -> None:
    """Open the TAR archive at archive_path and extract every entry into the existing
    directory dest_dir, preserving the directory structure stored in the archive.
    """
    if not os.path.exists(dest_dir):
        raise FileNotFoundError(f"destination directory does not exist: {dest_dir!r}")
    if not os.path.isdir(dest_dir):
        raise NotADirectoryError(f"destination is not a directory: {dest_dir!r}")

    dest_real = os.path.realpath(dest_dir)

    with tarfile.open(archive_path, mode="r:*") as tar:
        if hasattr(tarfile, "data_filter"):
            tar.extractall(path=dest_real, filter="data")
            return

        for member in tar:
            rel = os.path.normpath(member.name) if member.name else "."
            if rel == ".":
                continue

            _check_member_static(member, dest_real)

            target = os.path.normpath(os.path.join(dest_real, member.name))
            _prepare_parent(target, dest_real)

            if member.islnk():
                source = os.path.normpath(os.path.join(dest_real, member.linkname))
                _prepare_parent(source, dest_real)

            if os.path.islink(target):
                os.unlink(target)

            info = member
            if member.isdir():
                info = copy.copy(member)
                info.mode = (member.mode or 0o755) | 0o700

            tar.extract(info, path=dest_real, set_attrs=True)
