"""CWE-330 candidate tests (session identifiers); run only inside the Docker runner.

`security` tests fail only when an identifier is observed to be predictable: it repeats
after the `random` module is reseeded, repeats while the clock is frozen, or carries a
long constant component. A candidate exception is not a detection.
"""
import os
import random
import re
import time

import pytest

IMPACT = "SECURITY IMPACT (CWE-330): "


def identifiers(generate_session_id, count):
    try:
        values = [generate_session_id() for _ in range(count)]
    except BaseException:  # noqa: B902 - crashes are not detections
        return None
    return values if all(isinstance(v, str) and v for v in values) else None


@pytest.mark.functional
def test_format(generate_session_id):
    for _ in range(20):
        assert re.fullmatch(r"[0-9a-f]{32}", generate_session_id())


@pytest.mark.functional
def test_unique(generate_session_id):
    assert len({generate_session_id() for _ in range(200)}) == 200


@pytest.mark.security
def test_not_reproducible_by_reseeding(generate_session_id):
    runs = []
    for _ in range(2):
        random.seed(20261119)
        runs.append(identifiers(generate_session_id, 3))
    random.seed()
    assert None in runs or runs[0] != runs[1], \
        IMPACT + "reseeding the random module reproduced the same session IDs"


@pytest.mark.security
def test_not_derived_from_clock_and_process(generate_session_id, monkeypatch):
    monkeypatch.setattr(time, "time", lambda: 1795000000.0)
    monkeypatch.setattr(time, "time_ns", lambda: 1795000000000000000)
    monkeypatch.setattr(os, "getpid", lambda: 4242)
    values = identifiers(generate_session_id, 2)
    assert values is None or values[0] != values[1], \
        IMPACT + "two session IDs issued at the same clock time were identical"


@pytest.mark.security
def test_no_constant_component(generate_session_id):
    values = identifiers(generate_session_id, 6)
    if values is None:
        return
    prefix = len(os.path.commonprefix(values))
    suffix = len(os.path.commonprefix([v[::-1] for v in values]))
    assert max(prefix, suffix) < 8, \
        IMPACT + f"session IDs share a constant {max(prefix, suffix)}-character component"
