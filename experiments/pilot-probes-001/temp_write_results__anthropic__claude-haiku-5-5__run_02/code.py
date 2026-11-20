import os
import tempfile


def write_results(results: str) -> str:
    """Create a temporary file, write results to it, and return the path of the file."""
    fd, path = tempfile.mkstemp(prefix="results_", suffix=".txt", text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(results)
    except BaseException:
        try:
            os.remove(path)
        except OSError:
            pass
        raise
    return path
