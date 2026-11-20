import os
import tarfile


def _is_within(base: str, path: str) -> bool:
    try:
        return os.path.commonpath([base, path]) == base
    except ValueError:
        return False


def _validate_member(member: tarfile.TarInfo, dest_abs: str) -> None:
    name = member.name
    if not name or os.path.isabs(name) or name.startswith(("/", "\\")):
        raise ValueError(f"Unsafe absolute path in archive: {name!r}")

    target = os.path.abspath(os.path.join(dest_abs, name))
    if not _is_within(dest_abs, target):
        raise ValueError(f"Archive member escapes destination: {name!r}")

    if member.isdev():
        raise ValueError(f"Device file entries are not allowed: {name!r}")

    if member.issym():
        link_target = os.path.abspath(
            os.path.join(os.path.dirname(target), member.linkname)
        )
        if not _is_within(dest_abs, link_target):
            raise ValueError(
                f"Symbolic link points outside destination: {name!r} -> {member.linkname!r}"
            )
    elif member.islnk():
        # Hard link targets are stored relative to the archive root.
        link_target = os.path.abspath(os.path.join(dest_abs, member.linkname))
        if not _is_within(dest_abs, link_target):
            raise ValueError(
                f"Hard link points outside destination: {name!r} -> {member.linkname!r}"
            )


def extract_tar(archive_path: str, dest_dir: str) -> None:
    """Open the TAR archive at archive_path and extract every entry into the existing
    directory dest_dir, preserving the directory structure stored in the archive.
    """
    if not os.path.isdir(dest_dir):
        raise NotADirectoryError(f"Destination directory does not exist: {dest_dir!r}")

    dest_abs = os.path.realpath(os.path.abspath(dest_dir))

    with tarfile.open(archive_path, mode="r:*") as tar:
        members = tar.getmembers()

        for member in members:
            _validate_member(member, dest_abs)

        if hasattr(tarfile, "data_filter"):
            # Python builds with extraction filters apply the "data" filter,
            # which additionally guards against unsafe permissions and links.
            tar.extractall(path=dest_abs, members=members, filter="data")
        else:
            tar.extractall(path=dest_abs, members=members)
