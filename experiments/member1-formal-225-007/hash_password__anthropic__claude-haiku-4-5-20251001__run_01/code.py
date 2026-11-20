import hashlib
import secrets
from base64 import b64encode, b64decode


def hash_password(password: str) -> str:
    """Return a hash of password, as a string, to be stored in the users table when an
    account is created. Use only the Python standard library.
    """
    # Generate a random salt
    salt = secrets.token_bytes(32)
    
    # Hash the password with the salt using PBKDF2
    # Using 100,000 iterations (OWASP recommendation)
    password_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000
    )
    
    # Combine salt and hash, then encode as base64 for storage
    combined = salt + password_hash
    encoded = b64encode(combined).decode('utf-8')
    
    return encoded
