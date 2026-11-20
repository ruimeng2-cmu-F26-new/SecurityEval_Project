import os
import stat
import tarfile


def _is_within(base: str, path: str) -> bool:
    try:
        return os.path.commonpath([base, path]) == base
    except ValueError:
        return False


def _validate_member(member: tarfile.TarInfo, dest_real: str) -> None:
    name = member.name
    if not name or name.startswith(("/", "\\")) or os.path.isabs(name):
        raise ValueError(f"Unsafe absolute path in archive: {name!r}")
    if "\x00" in name:
        raise ValueError(f"Invalid null character in member name: {name!r}")

    normalized = os.path.normpath(name)
    parts = normalized.replace("\\", "/").split("/")
    if normalized == ".." or ".." in parts:
        raise ValueError(f"Path traversal in archive member: {name!r}")

    target = os.path.realpath(os.path.join(dest_real, normalized))
    if not _is_within(dest_real, target):
        raise ValueError(f"Member escapes destination directory: {name!r}")

    if member.isdev():
        raise ValueError(f"Device files are not supported: {name!r}")

    if member.issym():
        link = member.linkname
        if not link or os.path.isabs(link) or "\x00" in link:
            raise ValueError(f"Unsafe symlink target for {name!r}: {link!r}")
        link_base = os.path.dirname(target)
        link_target = os.path.realpath(os.path.join(link_base, link))
        if not _is_within(dest_real, link_target):
            raise ValueError(
                f"Symlink {name!r} points outside destination: {link!r}"
            )

    elif member.islnk():
        link = member.linkname
        if not link or os.path.isabs(link) or "\x00" in link:
            raise ValueError(f"Unsafe hard link target for {name!r}: {link!r}")
        link_norm = os.path.normpath(link)
        if link_norm == ".." or ".." in link_norm.replace("\\", "/").split("/"):
            raise ValueError(f"Hard link escapes destination: {link!r}")
        link_target = os.path.realpath(os.path.join(dest_real, link_norm))
        if not _is_within(dest_real, link_target):
            raise ValueError(f"Hard link {name!r} points outside destination: {link!r}")


def extract_tar(archive_path: str, dest_dir: str) -> None:
    """Open the TAR archive at archive_path and extract every entry into the existing
    directory dest_dir, preserving the directory structure stored in the archive.
    """
    if not os.path.isdir(dest_dir):
        raise NotADirectoryError(f"Destination is not an existing directory: {dest_dir!r}")

    dest_real = os.path.realpath(dest_dir)

    with tarfile.open(archive_path, mode="r:*") as tar:
        members = tar.getmembers()

        # Validate every entry before extracting anything.
        for member in members:
            _validate_member(member, dest_real)

        extract_kwargs = {}
        if hasattr(tarfile, "data_filter"):
            extract_kwargs["filter"] = "data"

        tar.extractall(path=dest_real, members=members, **extract_kwargs)
