import os
import tarfile


def _is_within(base: str, target: str) -> bool:
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
        safe_members = []
        for member in tar.getmembers():
            name = member.name
            if os.path.isabs(name) or name.startswith(("/", "\\")):
                raise ValueError(f"Unsafe absolute path in archive: {name}")
            parts = name.replace("\\", "/").split("/")
            if ".." in parts:
                raise ValueError(f"Unsafe path in archive: {name}")

            target = os.path.realpath(os.path.join(base, name))
            if not _is_within(base, target):
                raise ValueError(f"Unsafe path in archive: {name}")

            if member.issym() or member.islnk():
                link = member.linkname
                if member.issym():
                    link_target = os.path.join(
                        os.path.dirname(os.path.join(base, name)), link
                    )
                else:
                    link_target = os.path.join(base, link)
                if os.path.isabs(link) or not _is_within(
                    base, os.path.realpath(link_target)
                ):
                    raise ValueError(f"Unsafe link in archive: {name}")
            elif member.isdev():
                continue

            safe_members.append(member)

        # Extract one by one, re-checking real paths to defend against
        # symlinks created earlier in the same archive.
        for member in safe_members:
            target = os.path.realpath(os.path.join(base, member.name))
            if not _is_within(base, target):
                raise ValueError(f"Unsafe path in archive: {member.name}")
            if hasattr(tarfile, "data_filter"):
                tar.extract(member, path=base, filter="data")
            else:
                tar.extract(member, path=base)
