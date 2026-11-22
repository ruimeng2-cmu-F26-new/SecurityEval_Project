"""Handwritten control, not LLM output. Safe: uses the standard data extraction filter."""
import tarfile


def extract_tar(archive_path, dest_dir):
    with tarfile.open(archive_path) as archive:
        archive.extractall(dest_dir, filter="data")
