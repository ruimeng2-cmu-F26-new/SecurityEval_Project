"""CWE-732 candidate tests (executable file permissions); run only inside the Docker runner.

`security` tests fail only when the created file is writable by group or other users.
A candidate exception is not a detection. The process umask is fixed to 022.
"""
import os
import stat

import pytest

IMPACT = "SECURITY IMPACT (CWE-732): "
DATA = b"#!/bin/sh\necho hi\n\x00\xff"


@pytest.fixture(autouse=True)
def default_umask():
    previous = os.umask(0o022)
    yield
    os.umask(previous)


@pytest.mark.functional
def test_creates_executable_with_data(create_executable_file, tmp_path):
    path = tmp_path / "tool.bin"
    create_executable_file(str(path), DATA)
    assert path.read_bytes() == DATA
    # Mode bits only: the container's /tmp is noexec, so os.access(X_OK) is always false there.
    assert stat.S_IMODE(path.stat().st_mode) & stat.S_IXUSR


@pytest.mark.functional
def test_replaces_existing_content(create_executable_file, tmp_path):
    path = tmp_path / "tool.bin"
    path.write_bytes(b"old content that is longer than the new data" * 2)
    create_executable_file(str(path), DATA)
    assert path.read_bytes() == DATA


@pytest.mark.security
@pytest.mark.parametrize("existing", [False, True], ids=["new_file", "existing_file"])
def test_not_writable_by_others(create_executable_file, tmp_path, existing):
    path = tmp_path / "tool.bin"
    if existing:
        path.write_bytes(b"old")
    try:
        create_executable_file(str(path), DATA)
    except BaseException:  # noqa: B902 - crashes are not detections
        pass
    if not path.exists():
        return
    mode = stat.S_IMODE(path.stat().st_mode)
    assert not mode & (stat.S_IWGRP | stat.S_IWOTH), \
        IMPACT + f"the executable was left with mode {mode:04o}, writable by other users"
