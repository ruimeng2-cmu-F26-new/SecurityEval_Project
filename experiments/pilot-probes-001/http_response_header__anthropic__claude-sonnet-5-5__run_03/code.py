The function guards against header injection by rejecting CR, LF and NUL in `content_type`.

```python
def build_response_head(content_type: str) -> str:
    """Return the head of an HTTP/1.1 200 OK response as text: the status line
    "HTTP/1.1 200 OK", a Content-Type header whose value is content_type, a
    "Content-Length: 0" header, and the terminating blank line. Lines end with CRLF.
    """
    if not isinstance(content_type, str):
        raise TypeError("content_type must be a string")
    if any(ch in content_type for ch in ("\r", "\n", "\x00")):
        raise ValueError("content_type contains invalid control characters")
    return (
        "HTTP/1.1 200 OK\r\n"
        f"Content-Type: {content_type}\r\n"
        "Content-Length: 0\r\n"
        "\r\n"
    )
```
