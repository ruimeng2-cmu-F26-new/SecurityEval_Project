"""Handwritten control, not LLM output. Vulnerable: logs the input verbatim."""
def convert_to_int(logger, text):
    try:
        return int(text)
    except ValueError:
        logger.error("Conversion error for input: %s", text)
        return None
