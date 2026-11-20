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
PREFIXES = ["sql", "command", "path", "eval", "tar", "random", "hash", "permission", "log", "html", "filter",
            "url", "redirect", "error", "xml", "link"]
RULE_FIXTURES = [f"{prefix}_{kind}.py" for prefix in PREFIXES for kind in ("unsafe", "safe")] + [
    "command_allowlisted.py", "log_converted.py", "url_pattern.py", "redirect_checked.py", "xml_checked.py",
    "link_checked.py", "no_findings.py"]
DYNAMIC_CONTROLS = Path(__file__).resolve().parents[1] / "fixtures/dynamic"


def expected(path: Path) -> set[tuple[str, int]]:
    return {(rule, number) for number, line in enumerate(path.read_text().splitlines(), 1)
            if "# expect:" in line for rule in re.findall(r"AST-[A-Z]+-\d+", line.split("# expect:")[1])}


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
    for prefix in PREFIXES:
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


@pytest.mark.parametrize("name,severities", [
    ("eval_unsafe.py", ["high"] * 4 + ["low"]), ("tar_unsafe.py", ["high"] * 3 + ["medium"]),
    ("random_unsafe.py", ["high"] * 3 + ["medium"]), ("permission_unsafe.py", ["high"] * 4 + ["medium", "high"]),
    ("log_converted.py", ["low"] * 3), ("html_unsafe.py", ["high"] * 5 + ["low"]),
    ("url_pattern.py", ["low"]), ("redirect_unsafe.py", ["high", "high", "medium", "high"]),
    ("redirect_checked.py", ["low", "low"]), ("error_unsafe.py", ["high"] * 4 + ["low"]),
    ("xml_checked.py", ["low"]), ("link_checked.py", ["low", "low"])])
def test_new_rule_severities(name, severities):
    assert [f["severity"] for f in ast_rules.scan((FIXTURES / name).read_bytes())] == severities


def test_script_filter_rule_lowers_severity_for_repeated_removal():
    once = "import re\n\ndef f(c):\n    return re.sub(r'<script>', '', c)\n"
    looped = "import re\n\ndef f(c):\n    while '<script' in c:\n        c = re.sub(r'<script>', '', c)\n    return c\n"
    assert [f["severity"] for f in ast_rules.scan(once)] == ["high"]
    assert [f["severity"] for f in ast_rules.scan(looped)] == ["medium"]


# (control, target rule, severities reported by that rule): every vulnerable control is reported
# at medium or above; safe controls are silent, except where the rule cannot prove a check.
@pytest.mark.parametrize("name,rule,severities", [
    ("eval_safe.py", "AST-EVAL-001", []), ("eval_unsafe.py", "AST-EVAL-001", ["high"]),
    ("eval_restricted_builtins.py", "AST-EVAL-001", ["high"]),
    ("tar_safe.py", "AST-TAR-001", []), ("tar_unsafe.py", "AST-TAR-001", ["high"]),
    ("session_safe.py", "AST-RAND-001", []), ("session_unsafe.py", "AST-RAND-001", ["high"]),
    ("session_uuid1_unsafe.py", "AST-RAND-001", ["high"]),
    ("hash_safe.py", "AST-HASH-001", []), ("hash_unsafe.py", "AST-HASH-001", ["high"]),
    ("hash_static_salt_unsafe.py", "AST-HASH-001", ["high"]),
    ("executable_safe.py", "AST-PERM-001", []), ("executable_unsafe.py", "AST-PERM-001", ["high"]),
    ("log_safe.py", "AST-LOG-001", ["low"]), ("log_unsafe.py", "AST-LOG-001", ["high"]),
    ("greeting_safe.py", "AST-HTML-001", []), ("greeting_unsafe.py", "AST-HTML-001", ["high"]),
    ("filter_safe.py", "AST-FILTER-001", ["medium", "medium"]), ("filter_unsafe.py", "AST-FILTER-001", ["high"]),
    ("url_safe.py", "AST-URL-001", []), ("url_unsafe.py", "AST-URL-001", ["high"]),
    ("url_regex_unsafe.py", "AST-URL-001", ["high"]),
    ("redirect_safe.py", "AST-REDIR-001", ["low"]), ("redirect_unsafe.py", "AST-REDIR-001", ["high"]),
    ("redirect_slash_unsafe.py", "AST-REDIR-001", ["medium"]),
    ("error_safe.py", "AST-ERR-001", []), ("error_unsafe.py", "AST-ERR-001", ["high"]),
    ("error_traceback_unsafe.py", "AST-ERR-001", ["high"]),
    ("xml_safe.py", "AST-XML-001", ["low"]), ("xml_unsafe.py", "AST-XML-001", ["high"]),
    ("link_safe.py", "AST-LINK-001", ["low"]), ("link_escaped_unsafe.py", "AST-LINK-001", ["high"]),
    ("link_unsafe.py", "AST-LINK-001", ["high"]),
    ("count_lines_safe.py", "AST-CMD-001", []), ("count_lines_unsafe.py", "AST-CMD-001", ["high"]),
    ("count_lines_joined_unsafe.py", "AST-CMD-001", ["high"]),
    # Known false positive: the rule sees SQL text built from input, not the allowlist before it.
    ("sql_list_safe.py", "AST-SQL-001", ["high"]), ("sql_list_unsafe.py", "AST-SQL-001", ["high"])])
def test_new_rules_on_member3_handwritten_controls(name, rule, severities):
    findings = ast_rules.scan((DYNAMIC_CONTROLS / name).read_bytes())
    assert [f["severity"] for f in findings if f["rule_id"] == rule] == severities


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
