import os
import tarfile


def _is_within_directory(directory: str, target: str) -> bool:
    abs_directory = os.path.realpath(directory)
    abs_target = os.path.realpath(target)
    try:
        return os.path.commonpath([abs_directory, abs_target]) == abs_directory
    except ValueError:
        return False


def extract_tar(archive_path: str, dest_dir: str) -> None:
    """Open the TAR archive at archive_path and extract every entry into the existing
    directory dest_dir, preserving the directory structure stored in the archive.
    """
    with tarfile.open(archive_path, "r:*") as tar:
        members = tar.getmembers()
        for member in members:
            target = os.path.join(dest_dir, member.name)
            if not _is_within_directory(dest_dir, target):
                raise ValueError(f"Unsafe path in archive: {member.name!r}")
            if member.issym() or member.islnk():
                link = member.linkname
                if member.issym():
                    link_target = os.path.join(os.path.dirname(target), link)
                else:
                    link_target = os.path.join(dest_dir, link)
                if os.path.isabs(link) or not _is_within_directory(dest_dir, link_target):
                    raise ValueError(f"Unsafe link in archive: {member.name!r}")
            if member.isdev():
                raise ValueError(f"Device file in archive: {member.name!r}")
        try:
            tar.extractall(path=dest_dir, members=members, filter="data")
        except TypeError:
            tar.extractall(path=dest_dir, members=members)
