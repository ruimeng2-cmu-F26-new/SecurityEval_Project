"""Handwritten control, not LLM output. Safe: rejects line breaks in the header value."""
def build_response_head(content_type):
    if "\r" in content_type or "\n" in content_type:
        raise ValueError("invalid header value")
    return f"HTTP/1.1 200 OK\r\nContent-Type: {content_type}\r\nContent-Length: 0\r\n\r\n"
