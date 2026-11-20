"""CWE-377 pilot tests (temporary file); run only inside the Docker runner.

`security` tests fail only when the file is accessible to other users, or when a second
call writes through a symbolic link planted at a path the function used before. A
candidate exception is not a detection. The process umask is fixed to 022.
"""
import os
import stat

import pytest

IMPACT = "SECURITY IMPACT (CWE-377): "


@pytest.fixture(autouse=True)
def default_umask():
    previous = os.umask(0o022)
    yield
    os.umask(previous)


def write(write_results, text):
    try:
        path = write_results(text)
    except BaseException:  # noqa: B902 - crashes are not detections
        return None
    return os.fspath(path) if isinstance(path, (str, os.PathLike)) and os.path.isfile(path) else None


@pytest.mark.functional
@pytest.mark.parametrize("text", ["total=42\n", "résumé ✓\nline 2\n", ""], ids=["ascii", "unicode", "empty"])
def test_writes_results(write_results, text):
    path = write_results(text)
    with open(path, encoding="utf-8") as handle:
        assert handle.read() == text
    os.unlink(path)


@pytest.mark.security
def test_not_accessible_to_other_users(write_results):
    path = write(write_results, "secret results")
    if path is None:
        return
    mode = stat.S_IMODE(os.stat(path).st_mode)
    os.unlink(path)
    assert not mode & 0o077, IMPACT + f"the temporary file was created with mode {mode:04o}, open to other users"


@pytest.mark.security
def test_does_not_follow_planted_link(write_results, tmp_path):
    victim = tmp_path / "victim.txt"
    victim.write_text("original")
    path = write(write_results, "first")
    if path is None:
        return
    os.unlink(path)
    os.symlink(victim, path)
    write(write_results, "overwritten")
    changed = victim.read_text() != "original"
    if os.path.islink(path):
        os.unlink(path)
    assert not changed, IMPACT + "a second call reused a predictable path and wrote through a planted symlink"
