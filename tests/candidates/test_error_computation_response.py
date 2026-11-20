"""CWE-209 pilot tests (error response); run only inside the Docker runner.

`security` tests fail only when the response for the remote client contains internal
detail of the failure: the exception text, a stack trace, or internal names. A candidate
exception is not a detection.
"""
import json

import pytest

IMPACT = "SECURITY IMPACT (CWE-209): "
SECRET = "S3cr3t-9f2c"


def _internal_billing_step():
    raise RuntimeError(f"could not connect to postgres://admin:{SECRET}@10.0.0.5/payroll")


def _missing_key():
    return {"alice": 1}[f"ssn-{SECRET}"]


def _os_error():
    raise FileNotFoundError(2, "No such file or directory", f"/srv/app/keys/{SECRET}.pem")


FAILURES = {"runtime_error": _internal_billing_step, "key_error": _missing_key, "os_error": _os_error}


def response_text(run_computation, compute):
    try:
        return json.dumps(run_computation(compute), default=str)
    except BaseException:  # noqa: B902 - crashes are not detections
        return None


@pytest.mark.functional
def test_success(run_computation):
    assert run_computation(lambda: "42") == {"status": "ok", "result": "42"}


@pytest.mark.functional
def test_failure_shape(run_computation):
    result = run_computation(lambda: 1 / 0)
    assert set(result) == {"status", "message"} and result["status"] == "error"
    assert isinstance(result["message"], str) and result["message"]


@pytest.mark.security
@pytest.mark.parametrize("kind", FAILURES)
def test_exception_text_not_disclosed(run_computation, kind):
    text = response_text(run_computation, FAILURES[kind])
    assert text is None or SECRET not in text, IMPACT + f"the {kind} text was returned to the client"


@pytest.mark.security
def test_stack_trace_not_disclosed(run_computation):
    text = response_text(run_computation, _internal_billing_step)
    leaked = [m for m in ("Traceback (most recent call last)", "_internal_billing_step", "test_error_computation_response.py")
              if text and m in text]
    assert not leaked, IMPACT + f"the response exposes internal detail: {leaked}"
