import os
import stat

def create_executable_file(path: str, data: bytes) -> None:
    """Create a binary file at path containing data and make it executable."""
    with open(path, 'wb') as f:
        f.write(data)
    
    # Make the file executable
    current_permissions = os.stat(path).st_mode
    os.chmod(path, current_permissions | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
