import os

def create_executable_file(path: str, data: bytes) -> None:
    """Create a binary file at path containing data and make it executable."""
    with open(path, 'wb') as f:
        f.write(data)
    os.chmod(path, os.stat(path).st_mode | 0o111)
