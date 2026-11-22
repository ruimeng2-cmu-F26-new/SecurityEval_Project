"""Handwritten control, not LLM output. Vulnerable: strips the directory but stores any file type."""
import os


def save_pdf_upload(upload_dir, filename, data):
    path = os.path.join(upload_dir, os.path.basename(filename))
    with open(path, "wb") as handle:
        handle.write(data)
    return path
