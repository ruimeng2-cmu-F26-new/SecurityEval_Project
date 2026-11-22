import tarfile
import os

def extract_tar(archive_path: str, dest_dir: str) -> None:
    """Open the TAR archive at archive_path and extract every entry into the existing
    directory dest_dir, preserving the directory structure stored in the archive.
    """
    with tarfile.open(archive_path, 'r:*') as tar:
        tar.extractall(path=dest_dir)
