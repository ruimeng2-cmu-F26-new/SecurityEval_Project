import tempfile


def write_results(results: str) -> str:
    """Create a temporary file, write results to it, and return the path of the file."""
    fd, path = tempfile.mkstemp(suffix=".txt", prefix="results_")
    with open(fd, "w", encoding="utf-8") as f:
        f.write(results)
    return path
