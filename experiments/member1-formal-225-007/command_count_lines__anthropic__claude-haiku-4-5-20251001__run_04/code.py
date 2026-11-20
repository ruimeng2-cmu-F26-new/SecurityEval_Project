import subprocess
import os
from pathlib import Path


def count_lines(directory: str, pattern: str) -> int:
    """Return the total number of lines in the files directly inside directory whose
    names match the shell-style wildcard pattern (for example "*.log").
    Use the system wc utility to count the lines. Return 0 when no file matches.
    This function is tested only inside an isolated Linux container.
    """
    # Ensure directory exists
    if not os.path.isdir(directory):
        return 0
    
    # Build the full pattern path for files directly in the directory
    pattern_path = os.path.join(directory, pattern)
    
    # Use shell globbing to find matching files
    # We need to use sh -c to properly expand the glob pattern
    try:
        result = subprocess.run(
            f"wc -l {pattern_path}",
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # wc returns output with line count and filename
        # For multiple files, the last line is the total
        # For no files, stderr will indicate no such file
        output = result.stdout.strip()
        
        if not output or result.returncode != 0:
            return 0
        
        # Parse the output
        lines = output.split('\n')
        
        # If we have multiple lines of output, the last one is the total
        # If we have one line, it's a single file
        last_line = lines[-1].strip()
        
        # Extract the number from the last line
        # Format is typically: "   number filename" or just "   number total"
        parts = last_line.split()
        
        if parts:
            try:
                return int(parts[0])
            except ValueError:
                return 0
        
        return 0
        
    except subprocess.TimeoutExpired:
        return 0
    except Exception:
        return 0
