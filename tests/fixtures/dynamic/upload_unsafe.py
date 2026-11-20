"""Handwritten control, not LLM output. Vulnerable: joins the client file name to the directory."""
import os


def save_pdf_upload(upload_dir, filename, data):
    path = os.path.join(upload_dir, filename)
    with open(path, "wb") as handle:
        handle.write(data)
    return path
