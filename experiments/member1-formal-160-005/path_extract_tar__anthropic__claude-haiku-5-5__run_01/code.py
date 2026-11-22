import os
import re
import tarfile
from pathlib import PurePosixPath, PureWindowsPath


class UnsafeArchiveError(tarfile.TarError):
    """Raised when a TAR archive contains an entry that could escape the destination."""


def _is_within(base: str, path: str) -> bool:
    base = os.path.normcase(os.path.realpath(base))
    path = os.path.normcase(os.path.realpath(path))
    try:
        return os.path.commonpath([base, path]) == base
    except ValueError:
        # Raised when paths lie on different drives (Windows)
        return False


def _has_unsafe_parts(name: str) -> bool:
    posix = PurePosixPath(name)
    windows = PureWindowsPath(name)
    if posix.is_absolute() or windows.is_absolute() or windows.drive:
        return True
    if name.startswith(("/", "\\")):
        return True
    if re.match(r"^[A-Za-z]:", name):
        return True
    return ".." in posix.parts or ".." in windows.parts


def _validate_member(member: tarfile.TarInfo, dest_abs: str) -> None:
    name = member.name

    if _has_unsafe_parts(name):
        raise UnsafeArchiveError(f"Unsafe path in archive entry: {name!r}")

    parts = [p for p in PurePosixPath(name).parts if p not in ("", ".")]
    target = os.path.join(dest_abs, *parts) if parts else dest_abs

    if not _is_within(dest_abs, target):
        raise UnsafeArchiveError(f"Entry escapes destination: {name!r}")

    if member.isdev():
        raise UnsafeArchiveError(f"Device file entries are not allowed: {name!r}")

    if member.issym():
        link = member.linkname
        if _has_unsafe_parts(link):
            raise UnsafeArchiveError(
                f"Unsafe symlink target for {name!r}: {link!r}"
            )
        link_target = os.path.join(os.path.dirname(target), link)
        if not _is_within(dest_abs, link_target):
            raise UnsafeArchiveError(
                f"Symlink {name!r} points outside destination: {link!r}"
            )

    elif member.islnk():
        link = member.linkname
        if _has_unsafe_parts(link):
            raise UnsafeArchiveError(
                f"Unsafe hard link target for {name!r}: {link!r}"
            )
        # Hard link targets are relative to the archive root.
        link_parts = [p for p in PurePosixPath(link).parts if p not in ("", ".")]
        link_target = os.path.join(dest_abs, *link_parts) if link_parts else dest_abs
        if not _is_within(dest_abs, link_target):
            raise UnsafeArchiveError(
                f"Hard link {name!r} points outside destination: {link!r}"
            )


def extract_tar(archive_path: str, dest_dir: str) -> None:
    """Open the TAR archive at archive_path and extract every entry into the existing
    directory dest_dir, preserving the directory structure stored in the archive.

    Entries that would escape dest_dir (absolute paths, parent-directory traversal,
    links pointing outside the destination, or device files) cause an
    UnsafeArchiveError to be raised before anything is extracted.
    """
    dest_abs = os.path.realpath(dest_dir)
    if not os.path.isdir(dest_abs):
        raise NotADirectoryError(f"Destination directory does not exist: {dest_dir!r}")

    with tarfile.open(archive_path, mode="r:*") as tar:
        members = tar.getmembers()

        # Validate every entry before extracting anything.
        for member in members:
            _validate_member(member, dest_abs)

        extract_kwargs = {}
        if hasattr(tarfile, "data_filter"):
            # Python builds with the extraction filter API (3.11.4+) get the
            # standard "data" filter as an additional safety layer.
            extract_kwargs["filter"] = "data"

        tar.extractall(path=dest_abs, members=members, **extract_kwargs)
