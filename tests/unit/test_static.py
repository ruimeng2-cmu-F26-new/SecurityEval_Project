"""Member 2 rule tests on hand-written fixtures (tests/fixtures/static), not model outputs."""
import json
import re
from pathlib import Path

import pytest

from security_eval.analyzers import ast_rules
from security_eval.analyzers.static import ASTAnalyzer, BanditAnalyzer
from security_eval.contracts import validate
from security_eval.static_runner import run_static

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures/static"
SAMPLE = {"sample_id": "rule_fixture"}
RULE_FIXTURES = ["sql_unsafe.py", "sql_safe.py", "command_unsafe.py", "command_safe.py", "command_allowlisted.py",
                 "path_unsafe.py", "path_safe.py", "no_findings.py"]
DYNAMIC_CONTROLS = Path(__file__).resolve().parents[1] / "fixtures/dynamic"


def expected(path: Path) -> set[tuple[str, int]]:
    return {(m.group(1), number) for number, line in enumerate(path.read_text().splitlines(), 1)
            if (m := re.search(r"# expect: (AST-[A-Z]+-\d+)", line))}


@pytest.mark.parametrize("name", RULE_FIXTURES)
def test_ast_rules_report_exactly_the_marked_lines(name):
    path = FIXTURES / name
    found = {(f["rule_id"], f["line"]) for f in ast_rules.scan(path.read_bytes())}
    assert found == expected(path)
    if name.endswith("_unsafe.py"):
        assert found, "unsafe fixture must trigger its rule"


def test_every_rule_has_unsafe_and_safe_fixture():
    marked = {rule for name in RULE_FIXTURES for rule, _ in expected(FIXTURES / name)}
    assert marked == {r.rule_id for r in ast_rules.RULES}
    for prefix in ("sql", "command", "path"):
        assert (FIXTURES / f"{prefix}_safe.py").exists() and (FIXTURES / f"{prefix}_unsafe.py").exists()


def test_command_rule_severity_distinguishes_shell_from_program_choice():
    severities = [f["severity"] for f in ast_rules.scan((FIXTURES / "command_unsafe.py").read_bytes())]
    assert sorted(severities) == ["high"] * 3 + ["medium"] * 5


def test_command_rule_lowers_severity_after_allowlist_comparison():
    findings = ast_rules.scan((FIXTURES / "command_allowlisted.py").read_bytes())
    assert [f["severity"] for f in findings] == ["low", "low"]


def test_path_rule_severity_distinguishes_missing_and_weak_checks():
    findings = ast_rules.scan((FIXTURES / "path_unsafe.py").read_bytes())
    assert [f["severity"] for f in findings] == ["high", "high", "high", "medium", "medium"]
    assert "symlinks" in findings[3]["message"] and "sibling" in findings[4]["message"]
    assert all(f["cwe"] == "CWE-022" for f in findings)


@pytest.mark.parametrize("name,expected", [
    ("sql_safe.py", []), ("path_safe.py", []), ("command_safe.py", ["low"]), ("sql_unsafe.py", ["high"])])
def test_rules_on_member3_handwritten_controls(name, expected):
    findings = ast_rules.scan((DYNAMIC_CONTROLS / name).read_bytes())
    assert [f["severity"] for f in findings] == expected


def test_ast_analyzer_contract_and_evidence(tmp_path):
    record = ASTAnalyzer(tmp_path).analyze(FIXTURES / "sql_unsafe.py", SAMPLE, "unit-test-only")
    validate("analysis", record)
    assert record["status"] == "completed" and len(record["findings"]) == 5
    assert all(f["cwe"] == "CWE-089" for f in record["findings"])
    assert json.loads((tmp_path / "ast_rules.json").read_text())["ruleset_version"] == ast_rules.RULESET_VERSION


def test_ast_analyzer_reports_syntax_error_without_raising(tmp_path):
    record = ASTAnalyzer(tmp_path).analyze(FIXTURES / "syntax_error.py", SAMPLE, "unit-test-only")
    assert record["status"] == "error" and record["error"]["type"] == "SyntaxError"


def test_ast_scan_never_executes_code():
    assert ast_rules.scan("raise SystemExit('must never execute')\n") == []


def test_bandit_reports_findings_with_original_metadata(tmp_path):
    record = BanditAnalyzer(tmp_path).analyze(FIXTURES / "sql_unsafe.py", SAMPLE, "unit-test-only")
    validate("analysis", record)
    assert record["status"] == "completed" and record["tool_version"].startswith("bandit ")
    b608 = [f for f in record["findings"] if f["rule_id"] == "B608"]
    assert b608 and all(f["cwe"] == "CWE-089" and f["line"] for f in b608)
    assert {"bandit.raw.json", "bandit.stderr.txt"} <= {p.name for p in tmp_path.iterdir()}


def test_bandit_no_findings_is_completed_not_error(tmp_path):
    record = BanditAnalyzer(tmp_path).analyze(FIXTURES / "no_findings.py", SAMPLE, "unit-test-only")
    assert record["status"] == "completed" and record["findings"] == [] and record["error"] is None


def test_bandit_syntax_error_is_reported_as_error(tmp_path):
    # Bandit itself exits 0 here and lists the file under "errors".
    record = BanditAnalyzer(tmp_path).analyze(FIXTURES / "syntax_error.py", SAMPLE, "unit-test-only")
    validate("analysis", record)
    assert record["status"] == "error" and record["error"]["type"] == "ScanError"


def test_run_static_batch_summary_and_bad_inputs(tmp_path):
    summary = run_static([FIXTURES, tmp_path / "missing.py"], tmp_path / "out")
    targets = {t["target"]: t for t in summary["targets"]}
    assert targets["no_findings"]["results"]["bandit"]["outcome"] == "no_findings"
    assert targets["syntax_error"]["results"]["ast"]["outcome"] == "error"
    assert targets["missing"]["input_error"]
    assert {f["tool"] for f in summary["findings"]} == {"bandit", "ast"}
    assert all(f["validation_status"] == "unverified" for f in summary["findings"])
    saved = json.loads((tmp_path / "out/static_summary.json").read_text())
    assert saved["findings"] == summary["findings"]
    validate("analysis", json.loads((tmp_path / "out/sql_unsafe/ast.json").read_text()))
    with pytest.raises(FileExistsError):
        run_static([FIXTURES / "no_findings.py"], tmp_path / "out")
