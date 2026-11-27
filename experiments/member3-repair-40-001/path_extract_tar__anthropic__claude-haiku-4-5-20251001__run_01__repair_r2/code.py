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
    dest_real = os.path.realpath(dest_dir)
    with tarfile.open(archive_path, 'r:*') as tar:
        safe_members = []
        for member in tar.getmembers():
            name = member.name
            if os.path.isabs(name) or name.startswith(("/", "\\")):
                raise ValueError(f"Unsafe absolute path in archive: {name}")
            parts = name.replace("\\", "/").split("/")
            if ".." in parts:
                raise ValueError(f"Unsafe path in archive: {name}")
            if member.isdev():
                raise ValueError(f"Device entries not allowed: {name}")
            target = os.path.join(dest_real, name)
            if not _is_within(dest_real, target):
                raise ValueError(f"Path escapes destination: {name}")
            if member.issym() or member.islnk():
                link = member.linkname
                if member.issym():
                    link_target = os.path.join(os.path.dirname(target), link)
                else:
                    link_target = os.path.join(dest_real, link)
                if os.path.isabs(link) or not _is_within(dest_real, link_target):
                    raise ValueError(f"Unsafe link in archive: {name}")
            safe_members.append(member)

        # Extract one at a time, re-checking real paths to defend against
        # symlinks created earlier in the same archive.
        for member in safe_members:
            target = os.path.join(dest_real, member.name)
            parent = os.path.dirname(target)
            if not _is_within(dest_real, parent):
                raise ValueError(f"Path escapes destination: {member.name}")
            if os.path.islink(target) and not member.isdir():
                os.unlink(target)
            try:
                tar.extract(member, path=dest_real, filter="data")
            except tarfile.FilterError as exc:
                raise ValueError(str(exc)) from exc
