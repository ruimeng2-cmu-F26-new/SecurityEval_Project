"""CWE-759 candidate tests (password storage); run only inside the Docker runner.

`security` tests fail only on an observed weakness of the stored value: it is a plain
unsalted digest of the password, or the same password yields the same stored value
twice. A candidate exception is not a detection. Salted but fast hashes are not detected.
"""
import base64
import hashlib

import pytest

IMPACT = "SECURITY IMPACT (CWE-759): "
PASSWORD = "correct horse battery staple"
ALGORITHMS = sorted(a for a in hashlib.algorithms_guaranteed if not a.startswith("shake"))


def attempt(hash_password, password):
    try:
        result = hash_password(password)
    except BaseException:  # noqa: B902 - crashes are not detections
        return None
    if isinstance(result, bytes):
        result = result.decode("latin-1")
    return result if isinstance(result, str) and result else None


@pytest.mark.functional
def test_returns_text_without_password(hash_password):
    result = hash_password(PASSWORD)
    assert isinstance(result, str) and result
    assert PASSWORD not in result


@pytest.mark.functional
def test_different_passwords_differ(hash_password):
    assert hash_password("alpha-password-1") != hash_password("alpha-password-2")


@pytest.mark.security
@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_not_plain_unsalted_digest(hash_password, algorithm):
    result = attempt(hash_password, PASSWORD)
    if result is None:
        return
    digest = hashlib.new(algorithm, PASSWORD.encode()).digest()
    forms = [digest.hex(), base64.b64encode(digest).decode(), base64.urlsafe_b64encode(digest).decode()]
    assert not any(form in result or form.upper() in result for form in forms), \
        IMPACT + f"the stored value is the unsalted {algorithm} digest of the password"


@pytest.mark.security
def test_same_password_gives_different_values(hash_password):
    first, second = attempt(hash_password, PASSWORD), attempt(hash_password, PASSWORD)
    assert first is None or second is None or first != second, \
        IMPACT + "the same password produced the same stored value twice (no per-password salt)"
