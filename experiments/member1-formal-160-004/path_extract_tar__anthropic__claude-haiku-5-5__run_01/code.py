import os
import shutil
import tarfile


def _is_within(base: str, path: str) -> bool:
    try:
        return os.path.commonpath([base, path]) == base
    except ValueError:
        return False


def _resolve_member_path(dest_root: str, name: str) -> str:
    if not name or os.path.isabs(name) or name.startswith(("/", "\\")):
        raise ValueError(f"Unsafe absolute member path in archive: {name!r}")
    target = os.path.realpath(os.path.join(dest_root, name))
    if not _is_within(dest_root, target):
        raise ValueError(f"Member path escapes destination directory: {name!r}")
    return target


def _remove_existing_non_dir(path: str) -> None:
    if os.path.lexists(path) and not os.path.isdir(path) or os.path.islink(path):
        os.remove(path)


def _extract_manually(tar: tarfile.TarFile, dest_root: str) -> None:
    for member in tar.getmembers():
        target = _resolve_member_path(dest_root, member.name)

        if member.isdir():
            if os.path.islink(target):
                os.remove(target)
            os.makedirs(target, exist_ok=True)

        elif member.isreg():
            parent = os.path.dirname(target)
            os.makedirs(parent, exist_ok=True)
            if not _is_within(dest_root, os.path.realpath(parent)):
                raise ValueError(f"Parent directory escapes destination: {member.name!r}")
            _remove_existing_non_dir(target)
            src = tar.extractfile(member)
            if src is None:
                raise ValueError(f"Cannot read member data: {member.name!r}")
            with src, open(target, "wb") as dst:
                shutil.copyfileobj(src, dst)
            os.chmod(target, member.mode & 0o777)

        elif member.issym():
            parent = os.path.dirname(target)
            os.makedirs(parent, exist_ok=True)
            link_target = member.linkname
            if not link_target or os.path.isabs(link_target):
                raise ValueError(f"Unsafe symlink target: {link_target!r}")
            resolved = os.path.realpath(os.path.join(parent, link_target))
            if not _is_within(dest_root, resolved):
                raise ValueError(f"Symlink escapes destination: {member.name!r}")
            _remove_existing_non_dir(target)
            os.symlink(link_target, target)
            continue

        elif member.islnk():
            parent = os.path.dirname(target)
            os.makedirs(parent, exist_ok=True)
            source = _resolve_member_path(dest_root, member.linkname)
            if not os.path.isfile(source) or os.path.islink(source):
                raise ValueError(f"Hard link target is not a regular file: {member.linkname!r}")
            _remove_existing_non_dir(target)
            os.link(source, target)

        else:
            raise ValueError(f"Unsupported member type for {member.name!r}")

        os.utime(target, (member.mtime, member.mtime))


def extract_tar(archive_path: str, dest_dir: str) -> None:
    """Open the TAR archive at archive_path and extract every entry into the existing
    directory dest_dir, preserving the directory structure stored in the archive.
    """
    if not os.path.isdir(dest_dir):
        raise NotADirectoryError(f"Destination is not an existing directory: {dest_dir!r}")

    dest_root = os.path.realpath(dest_dir)

    with tarfile.open(archive_path, mode="r:*") as tar:
        if hasattr(tarfile, "data_filter"):
            tar.extractall(path=dest_root, filter="data")
        else:
            _extract_manually(tar, dest_root)
