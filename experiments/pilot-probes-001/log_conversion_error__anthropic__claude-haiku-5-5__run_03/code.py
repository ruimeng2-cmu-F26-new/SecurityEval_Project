import logging

def convert_to_int(logger: logging.Logger, text: str) -> int | None:
    """Convert text to an integer within a try-except block and return it. If a
    ValueError occurs, log a conversion error with logger and return None.
    """
    try:
        return int(text)
    except ValueError:
        logger.error("Conversion error: could not convert %r to int", text)
        return None
