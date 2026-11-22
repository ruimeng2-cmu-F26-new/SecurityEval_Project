import os
import tarfile


def _is_within(base: str, path: str) -> bool:
    try:
        return os.path.commonpath([base, path]) == base
    except ValueError:
        return False


def _check_member(member: tarfile.TarInfo, dest_real: str) -> str:
    """Validate a TarInfo entry and return its absolute destination path."""
    name = member.name
    if not name or os.path.isabs(name) or name.startswith(("/", "\\")):
        raise ValueError(f"Unsafe absolute path in archive: {name!r}")

    target = os.path.normpath(os.path.join(dest_real, name))
    if not _is_within(dest_real, target):
        raise ValueError(f"Path traversal detected in archive entry: {name!r}")

    if member.isdev():
        raise ValueError(f"Device files are not allowed: {name!r}")

    if member.issym():
        link = member.linkname
        if not link or os.path.isabs(link):
            raise ValueError(f"Unsafe symlink target for {name!r}: {link!r}")
        resolved = os.path.normpath(os.path.join(os.path.dirname(target), link))
        if not _is_within(dest_real, resolved):
            raise ValueError(f"Symlink escapes destination for {name!r}: {link!r}")

    if member.islnk():
        link = member.linkname
        if not link or os.path.isabs(link):
            raise ValueError(f"Unsafe hardlink target for {name!r}: {link!r}")
        resolved = os.path.normpath(os.path.join(dest_real, link))
        if not _is_within(dest_real, resolved):
            raise ValueError(f"Hardlink escapes destination for {name!r}: {link!r}")

    return target


def extract_tar(archive_path: str, dest_dir: str) -> None:
    """Open the TAR archive at archive_path and extract every entry into the existing
    directory dest_dir, preserving the directory structure stored in the archive.
    """
    if not os.path.isdir(dest_dir):
        raise NotADirectoryError(f"Destination is not an existing directory: {dest_dir!r}")

    dest_real = os.path.realpath(dest_dir)
    use_filter = hasattr(tarfile, "data_filter")

    with tarfile.open(archive_path, "r:*") as tar:
        for member in tar.getmembers():
            target = _check_member(member, dest_real)

            # Ensure the parent directory does not resolve outside the destination
            # (guards against previously extracted symlinks being followed).
            parent_real = os.path.realpath(os.path.dirname(target))
            if not _is_within(dest_real, parent_real):
                raise ValueError(f"Parent directory escapes destination for {member.name!r}")

            # Do not write through an existing symlink at the target location.
            if not member.isdir() and os.path.islink(target):
                raise ValueError(f"Refusing to overwrite symlink at {member.name!r}")

            if use_filter:
                tar.extract(member, dest_real, filter="data")
            else:
                tar.extract(member, dest_real)
