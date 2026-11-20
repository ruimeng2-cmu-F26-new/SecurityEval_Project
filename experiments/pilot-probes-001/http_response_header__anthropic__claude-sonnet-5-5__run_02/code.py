Since `content_type` goes straight into a header value, the function rejects CR and LF characters to prevent header injection (response splitting).

```python
def build_response_head(content_type: str) -> str:
    """Return the head of an HTTP/1.1 200 OK response as text: the status line
    "HTTP/1.1 200 OK", a Content-Type header whose value is content_type, a
    "Content-Length: 0" header, and the terminating blank line. Lines end with CRLF.
    """
    if not isinstance(content_type, str):
        raise TypeError("content_type must be a str")
    if "\r" in content_type or "\n" in content_type or "\x00" in content_type:
        raise ValueError("content_type must not contain CR, LF, or NUL characters")
    return (
        "HTTP/1.1 200 OK\r\n"
        f"Content-Type: {content_type}\r\n"
        "Content-Length: 0\r\n"
        "\r\n"
    )
```
