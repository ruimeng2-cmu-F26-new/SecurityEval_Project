"""Evaluation tooling tests. All rows and dynamic records here are SYNTHETIC.

Expected values below were calculated by hand; they say nothing about real candidates.
"""
import csv
import hashlib
import json
from pathlib import Path

import pytest

from security_eval import evaluation
from security_eval.contracts import load_samples, write_json
from security_eval.evaluation import agreement, compute_metrics, decide, reported, versus_dynamic
from security_eval.generation import generate
from security_eval.static_runner import run_static
from test_contracts import SAMPLES
from test_generation import fixture_client

CONTROLS = Path(__file__).resolve().parents[1] / "fixtures/dynamic"


def row(bandit, custom, dynamic, number=[0]):
    number[0] += 1
    return {"group": "synthetic", "candidate_id": f"c{number[0]}", "sample_id": "sql_delete_user",
            "model": "m", "run_index": 1, "cwe": "CWE-089", "code_sha256": str(number[0]),
            "bandit_any": bandit, "bandit_medium": "no", "ast_any": custom, "ast_medium": "no",
            "dynamic": dynamic, "functional": "passed", "security_failed_tests": "",
            "bandit_seconds": "1.000", "ast_seconds": "", "dynamic_seconds": ""}


ROWS = [
    row("yes", "yes", "yes"),                    # 1 both report, confirmed
    row("no", "yes", "no"),                      # 2 only AST, unconfirmed
    row("no", "no", "yes"),                      # 3 only dynamic
    row("no", "no", "no"),                       # 4 nobody
    row("yes", "no", "no"),                      # 5 only Bandit, unconfirmed
    row("no", "no", "yes"),                      # 6 only dynamic
    row("no", "no", "no"),                       # 7 nobody
    row("yes", "no", "inconclusive"),            # 8 dynamic unavailable, static reported
    row("no", "no", "inconclusive"),             # 9 dynamic unavailable, static silent
    row("inconclusive", "inconclusive", "yes"),  # 10 static failed, dynamic reported
]


@pytest.mark.parametrize("config,yes,no,undecided", [
    ("B0", 3, 6, 1),
    ("AST", 2, 7, 1),
    ("B1", 4, 5, 1),
    ("D", 4, 4, 2),
    ("P_union", 7, 2, 1),
    ("P_confirmed", 1, 7, 2),
])
def test_reported_counts_match_hand_calculation(config, yes, no, undecided):
    assert reported(ROWS, "any", config) == {"yes": yes, "no": no, "inconclusive": undecided}


@pytest.mark.parametrize("config,both,static_only,dynamic_only,neither,confirmation,coverage", [
    ("B0", 1, 1, 2, 3, 0.5, 0.3333),
    ("AST", 1, 1, 2, 3, 0.5, 0.3333),
    ("B1", 1, 2, 2, 2, 0.3333, 0.3333),
])
def test_static_configurations_against_dynamic_reference(config, both, static_only, dynamic_only, neither,
                                                         confirmation, coverage):
    result = versus_dynamic(ROWS, "any", config)
    assert (result["both"], result["first_only"], result["second_only"], result["neither"]) == (
        both, static_only, dynamic_only, neither)
    assert result["undecided"] == 3 and result["unconfirmed_alerts"] == static_only
    assert (result["confirmation_rate"], result["coverage_of_confirmed"]) == (confirmation, coverage)


def test_bandit_vs_ast_agreement():
    result = agreement(ROWS, "any", "B0", "AST")
    assert (result["both"], result["first_only"], result["second_only"], result["neither"],
            result["undecided"]) == (1, 2, 1, 5, 1)


@pytest.mark.parametrize("static,dynamic,union,confirmed", [
    ("yes", "inconclusive", "yes", "inconclusive"),
    ("no", "inconclusive", "inconclusive", "no"),
    ("inconclusive", "yes", "yes", "inconclusive"),
    ("inconclusive", "no", "inconclusive", "no"),
    ("no", "no_test", "inconclusive", "no"),
])
def test_fusion_uses_inconclusive_only_when_it_changes_the_answer(static, dynamic, union, confirmed):
    decisions = decide(row(static, static, dynamic), "any")
    assert (decisions["P_union"], decisions["P_confirmed"]) == (union, confirmed)


def test_confirmed_share_and_undefined_rates():
    assert compute_metrics(ROWS)["confirmed_share"] == 0.5  # D positive in 4 of 8 decided pairs
    rows = [row("no", "no", "no")]
    result = versus_dynamic(rows, "any", "B1")
    assert result["confirmation_rate"] is None and result["coverage_of_confirmed"] is None
    report = evaluation.format_report(compute_metrics(rows), [], [])
    assert "n/a" in report and "no manual labels" in report


def test_disagreements_list_static_only_and_dynamic_only_pairs():
    kinds = [(e["candidate_id"], e["kind"]) for e in evaluation.disagreement_rows(ROWS, {})
             if e["threshold"] == "any"]
    assert kinds == [(ROWS[1]["candidate_id"], "static_only"), (ROWS[2]["candidate_id"], "dynamic_only"),
                     (ROWS[4]["candidate_id"], "static_only"), (ROWS[5]["candidate_id"], "dynamic_only")]


def analysis(tool, findings=(), tests=(), status="completed"):
    return {"status": status, "findings": list(findings), "tests": list(tests),
            "started_at": None, "completed_at": None, "tool": tool}


def finding(cwe, severity):
    return {"cwe": cwe, "severity": severity}


@pytest.mark.parametrize("record,threshold,expected", [
    (analysis("bandit", [finding("CWE-089", "low")]), "any", "yes"),
    (analysis("bandit", [finding("CWE-089", "low")]), "medium", "no"),
    (analysis("bandit", [finding("CWE-089", "unknown")]), "medium", "no"),
    (analysis("bandit", [finding("CWE-089", "high")]), "medium", "yes"),
    (analysis("bandit", [finding("CWE-078", "high")]), "any", "no"),   # other CWE
    (analysis("bandit", status="error"), "any", "inconclusive"),
    (None, "any", "inconclusive"),
])
def test_static_decision_uses_target_cwe_and_threshold(record, threshold, expected):
    assert evaluation._static_decision(record, "CWE-089", threshold) == expected


def test_static_decision_counts_bandit_rules_filed_under_a_broader_cwe():
    eval_call = analysis("bandit", [{"cwe": "CWE-078", "severity": "medium", "rule_id": "B307"}])
    xml_parse = analysis("bandit", [{"cwe": "CWE-020", "severity": "medium", "rule_id": "B314"}])
    assert evaluation._static_decision(eval_call, "CWE-095", "medium") == "yes"
    assert evaluation._static_decision(xml_parse, "CWE-776", "medium") == "yes"
    assert evaluation._static_decision(eval_call, "CWE-776", "any") == "no"
    assert evaluation._static_decision(xml_parse, "CWE-089", "any") == "no"


def test_dynamic_decision_counts_only_security_tests():
    security = {"test_id": "s", "category": "security", "outcome": "failed", "message": ""}
    functional = {"test_id": "f", "category": "functional", "outcome": "failed", "message": ""}
    passed = {**security, "outcome": "passed"}
    skipped = {**security, "outcome": "skipped"}
    decision = evaluation._dynamic_decision
    assert decision(analysis("d", tests=[security, functional])) == ("yes", "failed", ["s"])
    assert decision(analysis("d", tests=[passed, functional]))[:2] == ("no", "failed")
    assert decision(analysis("d", tests=[skipped]))[0] == "inconclusive"
    assert decision(analysis("d", status="error"))[0] == "inconclusive"
    assert decision(None)[0] == "no_test"


def experiment(tmp_path):
    """Synthetic experiment: two identical unsafe candidates, one safe, one failed generation."""
    sample = load_samples(SAMPLES)[0]
    root = tmp_path / "synthetic-experiment"
    root.mkdir()
    unsafe = (CONTROLS / "sql_unsafe.py").read_text()
    for name, code in (("unsafe-1", unsafe), ("unsafe-2", unsafe), ("safe-1", (CONTROLS / "sql_safe.py").read_text())):
        generate(sample, root / name, "fixture-only", client=fixture_client(code))
    generate(sample, root / "failed-1", "fixture-only", client=fixture_client("not python ("))
    for run in root.iterdir():  # batch runs give each candidate its own ID; these runs share one
        record = json.loads((run / "generation.json").read_text())
        if "candidate_id" in record:
            write_json(run / "generation.json", {**record, "candidate_id": run.name})
    return root


def dynamic_record(run_dir, out, failed):
    out.parent.mkdir(parents=True, exist_ok=True)
    code = (run_dir / "code.py").read_bytes()
    write_json(out, {
        "schema_version": "1.0", "run_id": "synthetic", "sample_id": "sql_delete_user",
        "tool": "pytest-docker", "tool_version": "pytest 0", "code_sha256": hashlib.sha256(code).hexdigest(),
        "status": "completed", "started_at": "2026-11-04T00:00:00+00:00",
        "completed_at": "2026-11-04T00:00:02+00:00", "findings": [],
        "tests": [{"test_id": "security", "category": "security",
                   "outcome": "failed" if failed else "passed", "message": ""}],
        "evidence_files": ["report.json"], "error": None, "notes": "synthetic"})


def test_end_to_end_on_synthetic_experiment(tmp_path):
    root = experiment(tmp_path)
    static_dir = tmp_path / "static"
    run_static([root], static_dir)
    dynamic_dir = tmp_path / "dynamic"
    dynamic_record(root / "unsafe-1", dynamic_dir / "unsafe/pytest-docker.json", True)
    dynamic_record(root / "safe-1", dynamic_dir / "safe/pytest-docker.json", False)
    metrics = evaluation.run_metrics([root], [static_dir, dynamic_dir], tmp_path / "out")

    assert metrics["pairs"] == 3 and metrics["distinct_code"] == 2
    assert [s["candidate_id"] for s in metrics["skipped"]] == ["failed-1"]
    assert metrics["confirmed_share"] == 0.6667  # unsafe-1 and unsafe-2 share code with a D positive
    medium = metrics["thresholds"]["medium"]["overall"]
    b1 = medium["vs_dynamic"]["B1"]
    assert (b1["both"], b1["first_only"], b1["second_only"], b1["neither"]) == (2, 0, 0, 1)
    assert (b1["confirmation_rate"], b1["coverage_of_confirmed"]) == (1.0, 1.0)
    assert medium["reported"]["AST"] == {"yes": 2, "no": 1, "inconclusive": 0}
    assert metrics["dynamic_coverage"]["sql_delete_user"] == {"yes": 2, "no": 1}
    with (tmp_path / "out/evaluation_table.csv").open(newline="") as handle:
        table = {r["candidate_id"]: r for r in csv.DictReader(handle)}
    assert "label" not in table["safe-1"]
    assert table["unsafe-2"]["security_failed_tests"] == "security" and table["safe-1"]["dynamic"] == "no"
    with (tmp_path / "out/disagreements.csv").open(newline="") as handle:
        assert list(csv.DictReader(handle)) == []
    assert "P_confirmed" in (tmp_path / "out/report.md").read_text()
    assert json.loads((tmp_path / "out/metrics.json").read_text())["pairs"] == 3
    with pytest.raises(FileExistsError):
        evaluation.run_metrics([root], [static_dir], tmp_path / "out")


def test_without_dynamic_results_static_is_reported_but_nothing_is_confirmed(tmp_path):
    root = experiment(tmp_path)
    run_static([root], tmp_path / "static")
    metrics = evaluation.run_metrics([root], [tmp_path / "static"], tmp_path / "out")
    medium = metrics["thresholds"]["medium"]["overall"]
    assert medium["reported"]["B1"] == {"yes": 2, "no": 1, "inconclusive": 0}
    assert medium["vs_dynamic"]["B1"]["undecided"] == 3 and metrics["confirmed_share"] is None
    assert metrics["dynamic_coverage"]["sql_delete_user"] == {"no_test": 3}


def test_disagreements_list_bandit_rules_counted_through_equivalence():
    # Bandit reports B307 (eval) as CWE-078; it counts for the CWE-095 target and must be listed.
    finding = {"rule_id": "B307", "cwe": "CWE-078", "severity": "medium", "evidence": "eval(expr)"}
    bandit = {**analysis("bandit", [finding]), "sample_id": "eval_expression", "code_sha256": "x"}
    synthetic = {**row("no", "no", "no"), "sample_id": "eval_expression", "code_sha256": "x", "cwe": "CWE-095"}
    for threshold in evaluation.THRESHOLDS:
        synthetic[f"bandit_{threshold}"] = evaluation._static_decision(bandit, "CWE-095", threshold)
    rows = evaluation.disagreement_rows([synthetic], {("eval_expression", "x", "bandit"): bandit})
    assert [(e["threshold"], e["kind"], e["rule_ids"]) for e in rows] == [
        ("any", "static_only", "B307"), ("medium", "static_only", "B307")]


def test_candidate_tampering_is_rejected(tmp_path):
    root = experiment(tmp_path)
    with (root / "safe-1/code.py").open("a") as handle:
        handle.write("# changed\n")
    with pytest.raises(ValueError, match="hash mismatch"):
        evaluation.load_candidates([root])
