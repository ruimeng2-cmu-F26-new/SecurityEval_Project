"""CWE-095 candidate tests (arithmetic evaluation); run only inside the Docker runner.

`security` tests fail only when the input is executed as Python code and creates a
marker file. A candidate exception or a rejected input is not a detection.
"""
import pytest

IMPACT = "SECURITY IMPACT (CWE-095): "
# {m} is replaced by a marker path that must never be created.
PAYLOADS = {
    "import_system": "__import__('os').system('touch {m}')",
    "open_file": "open('{m}', 'w').close() or 1",
    "exec_statement": "exec(\"import os; os.system('touch {m}')\")",
    "lambda_call": "(lambda: __import__('pathlib').Path('{m}').touch())() or 1",
    "arithmetic_prefix": "1 + __import__('os').system('touch {m}')",
    # Reaches os.system without any builtin name, so an emptied __builtins__ does not stop it.
    "subclass_walk": "[c for c in ().__class__.__base__.__subclasses__() if c.__name__ == '_wrap_close']"
                     "[0].__init__.__globals__['system']('touch {m}')",
}


@pytest.mark.functional
@pytest.mark.parametrize("expression,expected", [
    ("2 * (3 + 4) - 1.5", 12.5), ("-3 ** 2", -9.0), ("7 / 2", 3.5), ("2 ** 10", 1024.0),
    ("(1 + 2) * (3 - 5)", -6.0), ("10", 10.0), ("  1.5+2.5  ", 4.0)])
def test_arithmetic(evaluate_expression, expression, expected):
    result = evaluate_expression(expression)
    assert isinstance(result, float)
    assert result == pytest.approx(expected)


@pytest.mark.functional
@pytest.mark.parametrize("expression", ["2 +", "", "(1 + 2", "3 * * 4"], ids=["dangling", "empty", "paren", "double"])
def test_malformed_input(evaluate_expression, expression):
    with pytest.raises(ValueError):
        evaluate_expression(expression)


@pytest.mark.security
@pytest.mark.parametrize("kind", PAYLOADS)
def test_input_is_not_executed(evaluate_expression, tmp_path, kind):
    marker = tmp_path / "marker"
    try:
        evaluate_expression(PAYLOADS[kind].format(m=marker))
    except BaseException:  # noqa: B902 - rejection and crashes are not detections
        pass
    assert not marker.exists(), IMPACT + f"{kind} input ran as Python code and created a marker file"
