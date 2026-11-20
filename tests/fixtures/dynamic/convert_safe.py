"""Handwritten control, not LLM output. Safe: logs the repr of the input."""
def convert_to_int(logger, text):
    try:
        return int(text)
    except ValueError:
        logger.error("Conversion error for input %r", text)
        return None
