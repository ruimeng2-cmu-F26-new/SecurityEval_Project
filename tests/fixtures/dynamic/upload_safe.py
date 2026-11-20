"""Handwritten control, not LLM output. Safe: base name only, .pdf extension and PDF signature required."""
import os


def save_pdf_upload(upload_dir, filename, data):
    name = os.path.basename(filename.replace("\\", "/"))
    if name != filename or not name.lower().endswith(".pdf") or not data.startswith(b"%PDF-"):
        raise ValueError("not a PDF upload")
    path = os.path.join(upload_dir, name)
    with open(path, "wb") as handle:
        handle.write(data)
    return path
