import os
import tarfile


def _is_within(base: str, path: str) -> bool:
    try:
        return os.path.commonpath([base, path]) == base
    except ValueError:
        return False


def _resolve(path: str) -> str:
    return os.path.realpath(os.path.abspath(path))


def extract_tar(archive_path: str, dest_dir: str) -> None:
    """Open the TAR archive at archive_path and extract every entry into the existing
    directory dest_dir, preserving the directory structure stored in the archive.
    """
    if not os.path.isdir(dest_dir):
        raise NotADirectoryError(f"Destination is not an existing directory: {dest_dir!r}")

    dest_root = _resolve(dest_dir)
    use_data_filter = hasattr(tarfile, "data_filter")

    with tarfile.open(archive_path, mode="r:*") as tar:
        for member in tar.getmembers():
            name = member.name

            if os.path.isabs(name):
                raise tarfile.TarError(f"Refusing absolute member path: {name!r}")

            target = _resolve(os.path.join(dest_root, name))
            # Resolve the parent as well so that already-extracted symlinks
            # cannot redirect writes outside the destination.
            parent = _resolve(os.path.dirname(target))
            if not _is_within(dest_root, target) or not _is_within(dest_root, parent):
                raise tarfile.TarError(f"Member escapes destination: {name!r}")

            if member.isdev():
                raise tarfile.TarError(f"Refusing device file member: {name!r}")

            if member.issym():
                link_target = member.linkname
                if os.path.isabs(link_target):
                    raise tarfile.TarError(
                        f"Refusing absolute symlink target for {name!r}: {link_target!r}"
                    )
                resolved_link = _resolve(os.path.join(os.path.dirname(target), link_target))
                if not _is_within(dest_root, resolved_link):
                    raise tarfile.TarError(
                        f"Symlink {name!r} points outside destination: {link_target!r}"
                    )

            if member.islnk():
                link_target = member.linkname
                if os.path.isabs(link_target):
                    raise tarfile.TarError(
                        f"Refusing absolute hardlink target for {name!r}: {link_target!r}"
                    )
                resolved_link = _resolve(os.path.join(dest_root, link_target))
                if not _is_within(dest_root, resolved_link):
                    raise tarfile.TarError(
                        f"Hardlink {name!r} points outside destination: {link_target!r}"
                    )

            if use_data_filter:
                tar.extract(member, path=dest_root, filter="data")
            else:
                tar.extract(member, path=dest_root)
