"""CWE-434 pilot tests (PDF upload); run only inside the Docker runner.

`security` tests fail only when a file that is not a PDF is stored under a script or
HTML name, or when a file is written outside upload_dir. A candidate exception or a
rejected upload is not a detection.
"""
import pytest

IMPACT = "SECURITY IMPACT (CWE-434): "
PDF = b"%PDF-1.7\n1 0 obj\n<<>>\nendobj\n%%EOF\n"
ACTIVE = {
    "python": ("shell.py", b"import os\nos.system('id')\n"),
    "php": ("shell.php", b"<?php system($_GET['c']); ?>"),
    "html": ("page.html", b"<script>alert(1)</script>"),
    "double_extension": ("report.pdf.php", b"<?php system($_GET['c']); ?>"),
    "upper_case": ("SHELL.PHP", b"<?php system($_GET['c']); ?>"),
    "shell": ("run.sh", b"#!/bin/sh\nid\n"),
}
ESCAPES = {"parent": "../escaped.pdf", "nested_parent": "docs/../../escaped.pdf", "absolute": "{outside}/escaped.pdf"}


@pytest.fixture
def area(tmp_path):
    uploads = tmp_path / "uploads"
    uploads.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    return uploads, outside, tmp_path


def names(directory):
    return {str(p.relative_to(directory)) for p in directory.rglob("*") if p.is_file()}


@pytest.mark.functional
@pytest.mark.parametrize("filename", ["report.pdf", "Annual Report 2026.pdf"])
def test_saves_pdf(save_pdf_upload, area, filename):
    uploads, _, _ = area
    path = save_pdf_upload(str(uploads), filename, PDF)
    saved = uploads / filename
    assert saved.read_bytes() == PDF
    assert str(path) in (str(saved), str(saved.resolve()))


@pytest.mark.security
@pytest.mark.parametrize("kind", ACTIVE)
def test_active_content_not_stored(save_pdf_upload, area, kind):
    uploads, _, _ = area
    filename, data = ACTIVE[kind]
    try:
        save_pdf_upload(str(uploads), filename, data)
    except BaseException:  # noqa: B902 - rejection and crashes are not detections
        pass
    stored = sorted(n for n in names(uploads) if not n.lower().endswith(".pdf"))
    assert not stored, IMPACT + f"{kind} upload was stored as {stored[0]!r}"


@pytest.mark.security
@pytest.mark.parametrize("kind", ESCAPES)
def test_nothing_written_outside_upload_dir(save_pdf_upload, area, kind):
    uploads, outside, root = area
    before = names(root) - {"uploads/" + n for n in names(uploads)}
    try:
        save_pdf_upload(str(uploads), ESCAPES[kind].format(outside=outside), PDF)
    except BaseException:  # noqa: B902 - rejection and crashes are not detections
        pass
    after = {n for n in names(root) if not n.startswith("uploads/")}
    assert after <= before, IMPACT + f"{kind} file name wrote {sorted(after - before)} outside upload_dir"
