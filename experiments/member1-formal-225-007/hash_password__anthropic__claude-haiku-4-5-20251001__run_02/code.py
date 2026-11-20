import hashlib
import secrets
import base64


def hash_password(password: str) -> str:
    """Return a hash of password, as a string, to be stored in the users table when an
    account is created. Use only the Python standard library.
    """
    salt = secrets.token_bytes(32)
    password_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000
    )
    return base64.b64encode(salt + password_hash).decode('utf-8')
