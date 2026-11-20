import os
import stat
import tarfile


def _is_within(path: str, root: str) -> bool:
    try:
        return os.path.commonpath([path, root]) == root
    except ValueError:
        return False


def _normalize_member_name(name: str) -> str:
    name = name.replace("\\", "/")
    parts = [p for p in name.split("/") if p not in ("", ".")]
    return "/".join(parts)


def _check_member(member: tarfile.TarInfo, dest_root: str, symlink_names: set) -> None:
    raw_name = member.name
    if not raw_name or os.path.isabs(raw_name) or raw_name.startswith(("/", "\\")):
        raise ValueError(f"Unsafe absolute path in archive: {raw_name!r}")

    norm = _normalize_member_name(raw_name)
    if not norm or norm.split("/")[0] == "..":
        if norm == "":
            return
        raise ValueError(f"Unsafe path in archive: {raw_name!r}")

    target = os.path.realpath(os.path.join(dest_root, norm))
    if not _is_within(target, dest_root):
        raise ValueError(f"Path escapes destination: {raw_name!r}")

    # Refuse to write through a symlink created earlier in this same archive.
    parts = norm.split("/")
    for i in range(1, len(parts)):
        if "/".join(parts[:i]) in symlink_names:
            raise ValueError(f"Path traverses archive symlink: {raw_name!r}")

    if member.isdev():
        raise ValueError(f"Device files are not extracted: {raw_name!r}")

    if member.issym():
        link = member.linkname
        if not link or os.path.isabs(link) or link.startswith(("/", "\\")):
            raise ValueError(f"Unsafe symlink target: {raw_name!r} -> {link!r}")
        link_target = os.path.realpath(
            os.path.join(os.path.dirname(os.path.join(dest_root, norm)), link)
        )
        if not _is_within(link_target, dest_root):
            raise ValueError(f"Symlink escapes destination: {raw_name!r} -> {link!r}")
        symlink_names.add(norm)

    elif member.islnk():
        link = member.linkname
        if not link or os.path.isabs(link) or link.startswith(("/", "\\")):
            raise ValueError(f"Unsafe hardlink target: {raw_name!r} -> {link!r}")
        link_target = os.path.realpath(os.path.join(dest_root, _normalize_member_name(link)))
        if not _is_within(link_target, dest_root):
            raise ValueError(f"Hardlink escapes destination: {raw_name!r} -> {link!r}")


def extract_tar(archive_path: str, dest_dir: str) -> None:
    """Open the TAR archive at archive_path and extract every entry into the existing
    directory dest_dir, preserving the directory structure stored in the archive.

    All members are validated before anything is written, so an unsafe archive
    (path traversal, absolute paths, escaping links, device files) is rejected
    without partially extracting it.
    """
    if not os.path.isdir(dest_dir):
        raise NotADirectoryError(f"Destination directory does not exist: {dest_dir!r}")

    dest_root = os.path.realpath(dest_dir)

    with tarfile.open(archive_path, mode="r:*") as tar:
        members = tar.getmembers()

        symlink_names: set = set()
        for member in members:
            _check_member(member, dest_root, symlink_names)

        if hasattr(tarfile, "data_filter"):
            tar.extractall(path=dest_root, members=members, filter="data")
        else:
            tar.extractall(path=dest_root, members=members)
