"""Handwritten control, not LLM output. Vulnerable: extracts every entry without checking its path."""
import tarfile


def extract_tar(archive_path, dest_dir):
    with tarfile.open(archive_path) as archive:
        archive.extractall(dest_dir)
