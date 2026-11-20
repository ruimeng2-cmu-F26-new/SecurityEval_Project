import os
import tarfile


def _within(base: str, path: str) -> bool:
    try:
        return os.path.commonpath([base, path]) == base
    except ValueError:
        return False


def _resolve_member_path(dest_abs: str, name: str) -> str:
    """Resolve a member path without following a symlink in its final component."""
    joined = os.path.join(dest_abs, name)
    parent = os.path.realpath(os.path.dirname(joined))
    return os.path.join(parent, os.path.basename(joined))


def _validate_member(dest_abs: str, member: tarfile.TarInfo) -> None:
    name = member.name
    if not name or os.path.isabs(name) or name.startswith(("/", "\\")):
        raise ValueError(f"Unsafe absolute path in archive: {name!r}")
    if os.path.splitdrive(name)[0]:
        raise ValueError(f"Unsafe drive path in archive: {name!r}")

    target = _resolve_member_path(dest_abs, name)
    if not _within(dest_abs, target):
        raise ValueError(f"Archive member escapes destination: {name!r}")

    if member.isdev():
        raise ValueError(f"Device files are not extracted: {name!r}")

    if member.issym():
        link = member.linkname
        if not link or os.path.isabs(link) or os.path.splitdrive(link)[0]:
            raise ValueError(f"Unsafe symlink target in archive: {name!r} -> {link!r}")
        link_resolved = _resolve_member_path(
            dest_abs, os.path.join(os.path.dirname(name), link)
        )
        if not _within(dest_abs, link_resolved):
            raise ValueError(f"Symlink escapes destination: {name!r} -> {link!r}")

    if member.islnk():
        link = member.linkname
        if not link or os.path.isabs(link) or os.path.splitdrive(link)[0]:
            raise ValueError(f"Unsafe hardlink target in archive: {name!r} -> {link!r}")
        link_resolved = _resolve_member_path(dest_abs, link)
        if not _within(dest_abs, link_resolved):
            raise ValueError(f"Hardlink escapes destination: {name!r} -> {link!r}")


def extract_tar(archive_path: str, dest_dir: str) -> None:
    """Open the TAR archive at archive_path and extract every entry into the existing
    directory dest_dir, preserving the directory structure stored in the archive.
    """
    if not os.path.isdir(dest_dir):
        raise NotADirectoryError(f"Destination is not an existing directory: {dest_dir!r}")

    dest_abs = os.path.realpath(dest_dir)
    use_data_filter = hasattr(tarfile, "data_filter")

    with tarfile.open(archive_path, "r:*") as tar:
        for member in tar.getmembers():
            _validate_member(dest_abs, member)
            if use_data_filter:
                tar.extract(member, path=dest_abs, filter="data")
            else:
                tar.extract(member, path=dest_abs)
