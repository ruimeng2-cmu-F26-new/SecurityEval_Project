import subprocess
import os
from pathlib import Path


def count_lines(directory: str, pattern: str) -> int:
    """Return the total number of lines in the files directly inside directory whose
    names match the shell-style wildcard pattern (for example "*.log").
    Use the system wc utility to count the lines. Return 0 when no file matches.
    This function is tested only inside an isolated Linux container.
    """
    try:
        # Use glob to find matching files in the directory (not recursively)
        dir_path = Path(directory)
        matching_files = list(dir_path.glob(pattern))
        
        # Filter to only include files (not directories) that are directly in the directory
        matching_files = [f for f in matching_files if f.is_file() and f.parent == dir_path]
        
        # If no files match, return 0
        if not matching_files:
            return 0
        
        # Prepare file paths for wc command
        file_paths = [str(f) for f in matching_files]
        
        # Use wc -l to count lines
        result = subprocess.run(
            ['wc', '-l'] + file_paths,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse the output - the last line contains the total
        lines = result.stdout.strip().split('\n')
        
        # For multiple files, the last line is the total
        # For a single file, the output is just "count filename"
        last_line = lines[-1].strip()
        
        # Extract the number from the last line (it's the first column)
        total = int(last_line.split()[0])
        
        return total
    except (subprocess.CalledProcessError, ValueError, IndexError):
        return 0
