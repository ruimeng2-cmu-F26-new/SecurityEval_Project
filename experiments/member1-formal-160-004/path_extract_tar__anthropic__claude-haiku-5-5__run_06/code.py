import os
import tarfile


def _within(base: str, path: str) -> bool:
    try:
        return os.path.commonpath([base, path]) == base
    except ValueError:
        return False


def _check_member(member: tarfile.TarInfo, base: str) -> None:
    name = member.name
    if not name or os.path.isabs(name) or name.startswith(("/", "\\")):
        raise ValueError(f"Unsafe absolute path in archive: {name!r}")

    parts = name.replace("\\", "/").split("/")
    if ".." in parts:
        raise ValueError(f"Path traversal in archive entry: {name!r}")

    if member.ischr() or member.isblk():
        raise ValueError(f"Device files are not extracted: {name!r}")

    target = os.path.realpath(os.path.join(base, name))
    if not _within(base, target):
        raise ValueError(f"Entry escapes destination directory: {name!r}")

    # Ensure the parent directory of the target, as it exists right now on
    # disk, does not resolve outside the destination (guards against
    # previously extracted symlinks being used to redirect writes).
    parent = os.path.realpath(os.path.dirname(os.path.join(base, name)))
    if not _within(base, parent):
        raise ValueError(f"Entry parent escapes destination directory: {name!r}")

    if member.issym():
        link = member.linkname
        if not link or os.path.isabs(link) or link.startswith(("/", "\\")):
            raise ValueError(f"Unsafe symlink target: {link!r}")
        resolved = os.path.realpath(os.path.join(os.path.dirname(target), link))
        if not _within(base, resolved):
            raise ValueError(f"Symlink points outside destination: {name!r} -> {link!r}")

    elif member.islnk():
        link = member.linkname
        if not link or os.path.isabs(link) or link.startswith(("/", "\\")):
            raise ValueError(f"Unsafe hardlink target: {link!r}")
        if ".." in link.replace("\\", "/").split("/"):
            raise ValueError(f"Hardlink target traversal: {link!r}")
        resolved = os.path.realpath(os.path.join(base, link))
        if not _within(base, resolved):
            raise ValueError(f"Hardlink points outside destination: {name!r} -> {link!r}")


def extract_tar(archive_path: str, dest_dir: str) -> None:
    """Open the TAR archive at archive_path and extract every entry into the existing
    directory dest_dir, preserving the directory structure stored in the archive.
    """
    if not os.path.isdir(dest_dir):
        raise NotADirectoryError(f"Destination is not an existing directory: {dest_dir!r}")

    base = os.path.realpath(dest_dir)
    has_data_filter = hasattr(tarfile, "data_filter")

    with tarfile.open(archive_path, "r:*") as tar:
        members = tar.getmembers()

        # Validate every entry before writing anything to disk.
        for member in members:
            _check_member(member, base)

        for member in members:
            # Re-check against the filesystem state produced by earlier entries.
            _check_member(member, base)
            if has_data_filter:
                tar.extract(member, path=base, filter="data")
            else:
                tar.extract(member, path=base)
