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
    base = os.path.realpath(dest_dir)
    with tarfile.open(archive_path, "r:*") as tar:
        members = tar.getmembers()
        safe_members = []
        for member in members:
            name = member.name
            if os.path.isabs(name) or name.startswith(("/", "\\")):
                raise ValueError(f"Unsafe absolute path in archive: {name!r}")
            parts = name.replace("\\", "/").split("/")
            if ".." in parts:
                raise ValueError(f"Unsafe path traversal in archive: {name!r}")
            target = os.path.join(base, name)
            if not _is_within(base, target):
                raise ValueError(f"Entry escapes destination: {name!r}")

            if member.issym() or member.islnk():
                link = member.linkname
                if os.path.isabs(link):
                    raise ValueError(f"Unsafe link target: {link!r}")
                if member.issym():
                    link_target = os.path.join(os.path.dirname(target), link)
                else:
                    link_target = os.path.join(base, link)
                if not _is_within(base, link_target):
                    raise ValueError(f"Link escapes destination: {name!r}")
            elif member.isdev():
                # Skip device nodes, fifos are also not regular content
                continue
            elif not (member.isfile() or member.isdir()):
                continue

            # Reset potentially dangerous metadata
            member.mode &= 0o777
            member.uid = member.gid = 0
            member.uname = member.gname = ""
            safe_members.append(member)

        try:
            tar.extractall(path=base, members=safe_members, filter="data")
        except TypeError:
            tar.extractall(path=base, members=safe_members)
