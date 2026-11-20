import os
import shutil
import stat
import tarfile


def _is_within(base: str, path: str) -> bool:
    try:
        return os.path.commonpath([base, path]) == base
    except ValueError:
        return False


def _resolve_member_path(dest_real: str, name: str) -> str:
    if not name or os.path.isabs(name) or os.path.splitdrive(name)[0]:
        raise tarfile.TarError(f"Unsafe absolute path in archive: {name!r}")
    if name.startswith(("/", "\\")):
        raise tarfile.TarError(f"Unsafe absolute path in archive: {name!r}")
    target = os.path.normpath(os.path.join(dest_real, name))
    if not _is_within(dest_real, target):
        raise tarfile.TarError(f"Path escapes destination: {name!r}")
    return target


def _check_parent_contained(dest_real: str, target: str) -> None:
    parent = os.path.dirname(target)
    os.makedirs(parent, exist_ok=True)
    if not _is_within(dest_real, os.path.realpath(parent)):
        raise tarfile.TarError(f"Parent directory escapes destination: {target!r}")


def _remove_existing(target: str) -> None:
    if os.path.islink(target) or (os.path.lexists(target) and not os.path.isdir(target)):
        os.unlink(target)
    elif os.path.isdir(target):
        raise IsADirectoryError(f"Cannot overwrite directory with file: {target!r}")


def extract_tar(archive_path: str, dest_dir: str) -> None:
    """Open the TAR archive at archive_path and extract every entry into the existing
    directory dest_dir, preserving the directory structure stored in the archive.
    """
    if not os.path.isdir(dest_dir):
        raise NotADirectoryError(f"Destination is not an existing directory: {dest_dir!r}")

    dest_real = os.path.realpath(dest_dir)
    dir_mtimes = []

    with tarfile.open(archive_path, mode="r:*") as tar:
        for member in tar.getmembers():
            target = _resolve_member_path(dest_real, member.name)

            if member.isdir():
                os.makedirs(target, exist_ok=True)
                if not _is_within(dest_real, os.path.realpath(target)):
                    raise tarfile.TarError(f"Directory escapes destination: {member.name!r}")
                os.chmod(target, stat.S_IMODE(member.mode) & 0o777)
                dir_mtimes.append((target, member.mtime))

            elif member.isreg():
                _check_parent_contained(dest_real, target)
                src = tar.extractfile(member)
                if src is None:
                    raise tarfile.TarError(f"Cannot read file member: {member.name!r}")
                _remove_existing(target)
                with src, open(target, "xb") as out:
                    shutil.copyfileobj(src, out)
                os.chmod(target, stat.S_IMODE(member.mode) & 0o777)
                os.utime(target, (member.mtime, member.mtime))

            elif member.issym():
                _check_parent_contained(dest_real, target)
                link = member.linkname
                if not link or os.path.isabs(link) or os.path.splitdrive(link)[0]:
                    raise tarfile.TarError(f"Unsafe symlink target: {link!r}")
                resolved = os.path.normpath(os.path.join(os.path.dirname(target), link))
                if not _is_within(dest_real, resolved):
                    raise tarfile.TarError(f"Symlink escapes destination: {member.name!r}")
                _remove_existing(target)
                os.symlink(link, target)

            elif member.islnk():
                _check_parent_contained(dest_real, target)
                source = _resolve_member_path(dest_real, member.linkname)
                if not os.path.isfile(source) or os.path.islink(source):
                    raise tarfile.TarError(
                        f"Hard link target missing or invalid: {member.linkname!r}"
                    )
                _remove_existing(target)
                os.link(source, target)

            else:
                raise tarfile.TarError(
                    f"Unsupported member type for {member.name!r}"
                )

    # Apply directory timestamps last so that extraction does not alter them.
    for path, mtime in reversed(dir_mtimes):
        os.utime(path, (mtime, mtime))
