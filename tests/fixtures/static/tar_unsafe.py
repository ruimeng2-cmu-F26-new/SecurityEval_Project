# HAND-WRITTEN RULE-TEST FIXTURE for AST-TAR-001 (not a SecurityEval sample or LLM output).
import os
import tarfile


def everything(archive_path, dest_dir):
    with tarfile.open(archive_path) as archive:
        archive.extractall(dest_dir)  # expect: AST-TAR-001


def one_by_one(archive_path, dest_dir):
    archive = tarfile.open(archive_path)
    for member in archive:
        archive.extract(member, dest_dir)  # expect: AST-TAR-001


def trusted_filter(archive_path, dest_dir):
    with tarfile.open(archive_path) as archive:
        archive.extractall(dest_dir, filter="fully_trusted")  # expect: AST-TAR-001


def name_check_only(archive_path, dest_dir):
    with tarfile.open(archive_path) as archive:
        for member in archive.getmembers():
            if ".." in member.name or os.path.isabs(member.name):
                continue
            archive.extract(member, dest_dir)  # expect: AST-TAR-001
