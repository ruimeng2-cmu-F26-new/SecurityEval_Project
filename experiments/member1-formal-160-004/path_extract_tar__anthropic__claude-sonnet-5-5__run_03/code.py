import os
import tarfile


def _is_within(base: str, target: str) -> bool:
    base = os.path.realpath(base)
    target = os.path.realpath(target)
    try:
        return os.path.commonpath([base, target]) == base
    except ValueError:
        return False


def extract_tar(archive_path: str, dest_dir: str) -> None:
    """Open the TAR archive at archive_path and extract every entry into the existing
    directory dest_dir, preserving the directory structure stored in the archive.
    """
    with tarfile.open(archive_path, "r:*") as tar:
        members = tar.getmembers()
        base = os.path.realpath(dest_dir)

        for member in members:
            target = os.path.join(base, member.name)
            if not _is_within(base, target):
                raise ValueError(f"Unsafe path in archive: {member.name!r}")
            if member.issym() or member.islnk():
                link = member.linkname
                if member.issym():
                    link_target = os.path.join(os.path.dirname(target), link)
                else:
                    link_target = os.path.join(base, link)
                if os.path.isabs(link) or not _is_within(base, link_target):
                    raise ValueError(f"Unsafe link in archive: {member.name!r}")
            if member.isdev():
                raise ValueError(f"Device file in archive: {member.name!r}")

        try:
            tar.extractall(path=base, members=members, filter="data")
        except TypeError:
            tar.extractall(path=base, members=members)
