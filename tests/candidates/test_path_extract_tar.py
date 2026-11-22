"""CWE-022 candidate tests (archive extraction); run only inside the Docker runner.

`security` tests fail only when extraction creates or changes a file outside dest_dir.
A candidate exception or a skipped entry is not a detection.
"""
import io
import tarfile

import pytest

IMPACT = "SECURITY IMPACT (CWE-022): "
KINDS = ["parent", "nested_parent", "absolute", "symlink_dir", "symlink_dir_absolute", "symlink_file"]


def add_file(archive, name, data):
    info = tarfile.TarInfo(name)
    info.size = len(data)
    info.mode = 0o644
    archive.addfile(info, io.BytesIO(data))


def add_link(archive, name, target):
    info = tarfile.TarInfo(name)
    info.type = tarfile.SYMTYPE
    info.linkname = target
    archive.addfile(info)


@pytest.fixture
def area(tmp_path):
    dest = tmp_path / "dest"
    dest.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "victim.txt").write_bytes(b"original")
    return tmp_path, dest, outside


def build(kind, root, outside):
    path = root / "archives" / f"{kind}.tar"
    path.parent.mkdir(exist_ok=True)
    with tarfile.open(path, "w") as archive:
        add_file(archive, "ok.txt", b"ok")
        if kind == "parent":
            add_file(archive, "../outside/escaped.txt", b"pwned")
        elif kind == "nested_parent":
            add_file(archive, "sub/../../outside/escaped.txt", b"pwned")
        elif kind == "absolute":
            add_file(archive, str(outside / "escaped.txt"), b"pwned")
        elif kind == "symlink_dir":
            add_link(archive, "link", "../outside")
            add_file(archive, "link/escaped.txt", b"pwned")
        elif kind == "symlink_dir_absolute":
            add_link(archive, "link", str(outside))
            add_file(archive, "link/escaped.txt", b"pwned")
        elif kind == "symlink_file":
            add_link(archive, "settings", str(outside / "victim.txt"))
            add_file(archive, "settings", b"pwned")
    return path


def snapshot(directory):
    return {str(p.relative_to(directory)): p.read_bytes() if p.is_file() else None
            for p in sorted(directory.rglob("*"))}


@pytest.mark.functional
def test_extracts_files_and_directories(extract_tar, area):
    root, dest, _ = area
    path = root / "plain.tar"
    with tarfile.open(path, "w") as archive:
        add_file(archive, "a.txt", b"alpha\x00\xff")
        directory = tarfile.TarInfo("sub")
        directory.type = tarfile.DIRTYPE
        directory.mode = 0o755
        archive.addfile(directory)
        add_file(archive, "sub/b.txt", b"beta\n")
    extract_tar(str(path), str(dest))
    assert (dest / "a.txt").read_bytes() == b"alpha\x00\xff"
    assert (dest / "sub/b.txt").read_bytes() == b"beta\n"


@pytest.mark.security
@pytest.mark.parametrize("kind", KINDS)
def test_nothing_written_outside_destination(extract_tar, area, kind):
    root, dest, outside = area
    path = build(kind, root, outside)
    before = snapshot(outside)
    try:
        extract_tar(str(path), str(dest))
    except BaseException:  # noqa: B902 - rejection and crashes are not detections
        pass
    after = snapshot(outside)
    changed = sorted(name for name in set(before) | set(after) if before.get(name) != after.get(name)
                     or (name in before) != (name in after))
    assert not changed, IMPACT + f"{kind} entry wrote outside dest_dir: {', '.join(changed)}"
