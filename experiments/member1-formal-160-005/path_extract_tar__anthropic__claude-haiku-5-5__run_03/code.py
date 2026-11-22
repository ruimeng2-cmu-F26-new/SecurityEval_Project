import os
import tarfile


def _is_within(base: str, path: str) -> bool:
    try:
        return os.path.commonpath([base, path]) == base
    except ValueError:
        return False


def _member_is_safe(member: tarfile.TarInfo, dest_real: str) -> bool:
    name = member.name
    if not name or os.path.isabs(name) or os.path.splitdrive(name)[0]:
        return False

    target = os.path.realpath(os.path.join(dest_real, name))
    if not _is_within(dest_real, target):
        return False

    if member.isdev():
        return False

    if member.issym():
        if os.path.isabs(member.linkname):
            return False
        link_base = os.path.dirname(os.path.join(dest_real, name))
        link_target = os.path.realpath(os.path.join(link_base, member.linkname))
        if not _is_within(dest_real, link_target):
            return False

    if member.islnk():
        if os.path.isabs(member.linkname):
            return False
        link_target = os.path.realpath(os.path.join(dest_real, member.linkname))
        if not _is_within(dest_real, link_target):
            return False

    return True


def extract_tar(archive_path: str, dest_dir: str) -> None:
    """Open the TAR archive at archive_path and extract every entry into the existing
    directory dest_dir, preserving the directory structure stored in the archive.
    """
    if not os.path.isdir(dest_dir):
        raise NotADirectoryError(f"Destination is not an existing directory: {dest_dir}")

    dest_real = os.path.realpath(dest_dir)

    with tarfile.open(archive_path, mode="r:*") as tar:
        members = tar.getmembers()

        for member in members:
            if not _member_is_safe(member, dest_real):
                raise tarfile.TarError(f"Unsafe archive member rejected: {member.name!r}")

        if hasattr(tarfile, "data_filter"):
            tar.extractall(path=dest_real, members=members, filter="data")
        else:
            tar.extractall(path=dest_real, members=members)
