"""Handwritten control, not LLM output. Vulnerable: formats the value into the head."""
def build_response_head(content_type):
    return f"HTTP/1.1 200 OK\r\nContent-Type: {content_type}\r\nContent-Length: 0\r\n\r\n"
