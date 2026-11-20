import os
import tarfile


def _resolve_within(base: str, path: str) -> str:
    """Return the real path of `path` after verifying it lies within `base`."""
    real_base = os.path.realpath(base)
    real_path = os.path.realpath(path)
    if os.path.commonpath([real_base, real_path]) != real_base:
        raise tarfile.TarError(f"Path escapes destination directory: {path!r}")
    return real_path


def _member_target(dest: str, name: str) -> str:
    """Compute the on-disk target for an archive member name, rejecting unsafe names."""
    if not name or os.path.isabs(name) or name.startswith(("/", "\\")):
        raise tarfile.TarError(f"Absolute member path rejected: {name!r}")
    if os.path.splitdrive(name)[0]:
        raise tarfile.TarError(f"Drive-qualified member path rejected: {name!r}")
    normalized = os.path.normpath(name)
    if normalized == ".." or normalized.startswith(".." + os.sep):
        raise tarfile.TarError(f"Parent-relative member path rejected: {name!r}")
    target = os.path.join(dest, normalized)
    # Validate that the parent directory (after creation) stays inside dest.
    parent = os.path.dirname(target)
    os.makedirs(parent, exist_ok=True)
    _resolve_within(dest, parent)
    return target


def extract_tar(archive_path: str, dest_dir: str) -> None:
    """Open the TAR archive at archive_path and extract every entry into the existing
    directory dest_dir, preserving the directory structure stored in the archive.
    """
    if not os.path.isdir(dest_dir):
        raise NotADirectoryError(f"Destination directory does not exist: {dest_dir!r}")

    dest = os.path.realpath(dest_dir)

    with tarfile.open(archive_path, mode="r:*") as tar:
        for member in tar.getmembers():
            if member.isdev():
                raise tarfile.TarError(f"Device file entries are not allowed: {member.name!r}")

            target = _member_target(dest, member.name)

            if member.issym():
                # Symlink targets are relative to the link's own directory.
                link_location = os.path.join(os.path.dirname(target), member.linkname)
                if os.path.isabs(member.linkname):
                    raise tarfile.TarError(
                        f"Absolute symlink target rejected: {member.name!r} -> {member.linkname!r}"
                    )
                _resolve_within(dest, link_location)
            elif member.islnk():
                # Hard link targets are archive-relative paths.
                if os.path.isabs(member.linkname):
                    raise tarfile.TarError(
                        f"Absolute hardlink target rejected: {member.name!r} -> {member.linkname!r}"
                    )
                link_source = os.path.join(dest, os.path.normpath(member.linkname))
                _resolve_within(dest, link_source)

            # Remove pre-existing symlinks at the target location so that writing
            # the member cannot follow a link out of the destination directory.
            if os.path.islink(target):
                os.unlink(target)

            if member.isdir() and os.path.isdir(target):
                # Existing real directory: nothing to remove; attributes applied below.
                pass

            tar.extract(member, path=dest, set_attrs=not member.issym())
