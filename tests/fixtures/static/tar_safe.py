# HAND-WRITTEN RULE-TEST FIXTURE for AST-TAR-001 (not a SecurityEval sample or LLM output).
import tarfile


def data_filter(archive_path, dest_dir):
    with tarfile.open(archive_path) as archive:
        archive.extractall(dest_dir, filter="data")


def named_filter(archive_path, dest_dir):
    with tarfile.open(archive_path) as archive:
        archive.extractall(dest_dir, filter=tarfile.data_filter)


def default_filter(archive_path, dest_dir):
    with tarfile.open(archive_path) as archive:
        archive.extraction_filter = tarfile.data_filter
        archive.extractall(dest_dir)


def list_only(archive_path):
    with tarfile.open(archive_path) as archive:
        return archive.getnames()
