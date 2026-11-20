import os
import subprocess
import fnmatch


def count_lines(directory: str, pattern: str) -> int:
    """Return the total number of lines in the files directly inside directory whose
    names match the shell-style wildcard pattern (for example "*.log").
    Use the system wc utility to count the lines. Return 0 when no file matches.
    This function is tested only inside an isolated Linux container.
    """
    try:
        # List all files directly in the directory
        entries = os.listdir(directory)
    except (FileNotFoundError, NotADirectoryError, PermissionError):
        return 0
    
    # Filter files that match the pattern and are regular files
    matching_files = []
    for entry in entries:
        if fnmatch.fnmatch(entry, pattern):
            full_path = os.path.join(directory, entry)
            if os.path.isfile(full_path):
                matching_files.append(full_path)
    
    # If no files match, return 0
    if not matching_files:
        return 0
    
    try:
        # Use wc -l to count lines in all matching files
        result = subprocess.run(
            ['wc', '-l'] + matching_files,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse the output: wc returns lines like "10 file.txt"
        # The last line contains the total when multiple files are given
        lines = result.stdout.strip().split('\n')
        
        if len(matching_files) == 1:
            # For a single file, the output is just "count filename"
            total_line = lines[0]
        else:
            # For multiple files, the last line is the total
            total_line = lines[-1]
        
        # Extract the number from "count filename" or "count total"
        count = int(total_line.split()[0])
        return count
    except (subprocess.CalledProcessError, ValueError, IndexError):
        return 0
