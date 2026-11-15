"""Evaluation tooling tests. All rows, labels and dynamic records here are SYNTHETIC.

Expected values below were calculated by hand; they say nothing about real candidates.
"""
import csv
import hashlib
import json
from pathlib import Path

import pytest

from security_eval import evaluation
from security_eval.contracts import load_samples, write_json
from security_eval.evaluation import compare, compute_metrics, decide, overlap, score
from security_eval.generation import generate
from security_eval.static_runner import run_static
from test_contracts import SAMPLES
from test_generation import fixture_client

CONTROLS = Path(__file__).resolve().parents[1] / "fixtures/dynamic"


def row(bandit, custom, dynamic, label, number=[0]):
    number[0] += 1
    return {"group": "synthetic", "candidate_id": f"c{number[0]}", "sample_id": "sql_delete_user",
            "model": "m", "run_index": 1, "cwe": "CWE-089", "code_sha256": str(number[0]),
            "bandit_any": bandit, "bandit_medium": "no", "ast_any": custom, "ast_medium": "no",
            "dynamic": dynamic, "functional": "passed", "security_failed_tests": "", "label": label,
            "bandit_seconds": "1.000", "ast_seconds": "", "dynamic_seconds": ""}


ROWS = [
    row("yes", "yes", "yes", "vulnerable"),            # both find it
    row("no", "yes", "no", "vulnerable"),              # only AST
    row("no", "no", "yes", "vulnerable"),              # only dynamic
    row("no", "no", "no", "vulnerable"),               # nobody
    row("yes", "no", "no", "not_vulnerable"),          # static false positive
    row("no", "no", "yes", "not_vulnerable"),          # dynamic false positive
    row("no", "no", "no", "not_vulnerable"),           # clean
    row("yes", "no", "inconclusive", "vulnerable"),    # dynamic unavailable, static reported
    row("no", "no", "inconclusive", "not_vulnerable"),  # dynamic unavailable, static silent
    row("yes", "yes", "yes", "uncertain"),
    row("yes", "yes", "yes", "unlabeled"),
]


@pytest.mark.parametrize("config,tp,fp,fn,tn,inconclusive,precision,recall", [
    ("B0", 2, 1, 3, 3, 0, 0.6667, 0.4),
    ("AST", 2, 0, 3, 4, 0, 1.0, 0.4),
    ("B1", 3, 1, 2, 3, 0, 0.75, 0.6),
    ("D", 2, 1, 2, 2, 2, 0.6667, 0.5),
    ("P_union", 4, 2, 1, 1, 1, 0.6667, 0.8),
    ("P_confirmed", 1, 0, 3, 4, 1, 1.0, 0.25),
])
def test_scores_match_hand_calculation(config, tp, fp, fn, tn, inconclusive, precision, recall):
    result = score(ROWS, "any", config)
    assert (result["tp"], result["fp"], result["fn"], result["tn"]) == (tp, fp, fn, tn)
    assert result["inconclusive"] == inconclusive and result["unlabeled_or_uncertain"] == 2
    assert result["precision"] == precision and result["recall"] == recall


def test_f1_and_false_positive_rate():
    result = score(ROWS, "any", "B1")
    assert result["f1"] == 0.6667 and result["false_positive_rate"] == 0.25


def test_f1_is_calculated_from_counts_not_rounded_ratios():
    rows = [row("yes", "no", "no", "vulnerable") for _ in range(4)]
    rows += [row("yes", "no", "no", "not_vulnerable") for _ in range(3)]
    assert score(rows, "any", "B1")["f1"] == 0.7273  # 8 / 11


@pytest.mark.parametrize("static,dynamic,union,confirmed", [
    ("yes", "inconclusive", "yes", "inconclusive"),
    ("no", "inconclusive", "inconclusive", "no"),
    ("inconclusive", "yes", "yes", "inconclusive"),
    ("inconclusive", "no", "inconclusive", "no"),
    ("no", "no_test", "inconclusive", "no"),
])
def test_fusion_uses_inconclusive_only_when_it_changes_the_answer(static, dynamic, union, confirmed):
    decisions = decide(row(static, static, dynamic, "vulnerable"), "any")
    assert (decisions["P_union"], decisions["P_confirmed"]) == (union, confirmed)


def test_overlap_excludes_undecided_rows():
    result = overlap(ROWS, "any", "B1", "D")
    assert result["vulnerable"] == {"first_only": 1, "second_only": 1, "both": 1, "neither": 1}
    assert result["not_vulnerable"] == {"first_only": 1, "second_only": 1, "both": 0, "neither": 1}


def test_union_comparison_shows_the_false_positive_cost_on_paired_rows():
    result = compare(ROWS, "any", "B1", "P_union")
    assert result["paired_rows"] == 8
    assert (result["tp_change"], result["fp_change"]) == (1, 1)
    assert (result["recall_change"], result["precision_change"]) == (0.2, -0.0833)


def test_confirmed_comparison_shows_the_recall_loss_on_paired_rows():
    result = compare(ROWS, "any", "B1", "P_confirmed")
    assert result["paired_rows"] == 8
    assert (result["tp_change"], result["fp_change"]) == (-1, -1)
    assert (result["recall_change"], result["precision_change"]) == (-0.25, 0.3333)


def test_zero_denominators_are_undefined_not_zero():
    rows = [row("no", "no", "no", "not_vulnerable")]
    result = score(rows, "any", "B1")
    assert result["precision"] is None and result["recall"] is None and result["f1"] is None
    assert compare(rows, "any", "B1", "P_union")["recall_change"] is None
    report = evaluation.format_report(compute_metrics(rows), [], [], None)
    assert "recall and false negatives cannot be evaluated" in report and "n/a" in report


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
    code = (run_dir / "code.py").read_bytes()
    write_json(out, {
        "schema_version": "1.0", "run_id": "synthetic", "sample_id": "sql_delete_user",
        "tool": "pytest-docker", "tool_version": "pytest 0", "code_sha256": hashlib.sha256(code).hexdigest(),
        "status": "completed", "started_at": "2026-11-04T00:00:00+00:00",
        "completed_at": "2026-11-04T00:00:02+00:00", "findings": [],
        "tests": [{"test_id": "security", "category": "security",
                   "outcome": "failed" if failed else "passed", "message": ""}],
        "evidence_files": ["report.json"], "error": None, "notes": "synthetic"})


def write_labels(path, labels):
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["candidate_id", "label"])
        writer.writerows(labels.items())


def test_end_to_end_on_synthetic_experiment(tmp_path):
    root = experiment(tmp_path)
    static_dir = tmp_path / "static"
    run_static([root], static_dir)
    dynamic_dir = tmp_path / "dynamic"
    dynamic_dir.mkdir()
    dynamic_record(root / "unsafe-1", dynamic_dir / "unsafe.json", True)
    (dynamic_dir / "unsafe.json").rename(dynamic_dir / "pytest-docker.json")
    labels = tmp_path / "labels.csv"
    write_labels(labels, {"unsafe-1": "vulnerable", "unsafe-2": "vulnerable", "safe-1": "not_vulnerable"})
    metrics = evaluation.run_metrics([root], [static_dir, dynamic_dir], tmp_path / "out", labels)

    assert metrics["pairs"] == 3 and metrics["distinct_code"] == 2
    assert [s["candidate_id"] for s in metrics["skipped"]] == ["failed-1"]
    overall = metrics["thresholds"]["medium"]["overall"]
    assert (overall["B1"]["tp"], overall["B1"]["tn"]) == (2, 1)
    assert overall["AST"]["recall"] == 1.0
    assert (overall["D"]["tp"], overall["D"]["inconclusive"]) == (2, 1)  # safe-1 has no dynamic record
    assert metrics["dynamic_coverage"]["sql_delete_user"] == {"yes": 2, "no_test": 1}
    with (tmp_path / "out/evaluation_table.csv").open(newline="") as handle:
        table = {r["candidate_id"]: r for r in csv.DictReader(handle)}
    assert table["unsafe-2"]["security_failed_tests"] == "security" and table["safe-1"]["dynamic"] == "no_test"
    assert "P_confirmed" in (tmp_path / "out/report.md").read_text()
    assert json.loads((tmp_path / "out/metrics.json").read_text())["pairs"] == 3
    with pytest.raises(FileExistsError):
        evaluation.run_metrics([root], [static_dir], tmp_path / "out", labels)


def test_error_analysis_lists_static_false_positives_and_negatives(tmp_path):
    root = experiment(tmp_path)
    run_static([root], tmp_path / "static")
    labels = tmp_path / "labels.csv"
    write_labels(labels, {"unsafe-1": "not_vulnerable", "safe-1": "vulnerable"})  # deliberately wrong
    evaluation.run_metrics([root], [tmp_path / "static"], tmp_path / "out", labels)
    with (tmp_path / "out/error_analysis.csv").open(newline="") as handle:
        errors = list(csv.DictReader(handle))
    kinds = {(e["candidate_id"], e["threshold"]): e for e in errors}
    assert kinds["unsafe-1", "medium"]["kind"] == "false_positive"
    assert "AST-SQL-001" in kinds["unsafe-1", "medium"]["rule_ids"]
    assert kinds["safe-1", "any"]["kind"] == "false_negative" and kinds["safe-1", "any"]["rule_ids"] == ""


def test_candidate_tampering_and_unknown_labels_are_rejected(tmp_path):
    root = experiment(tmp_path)
    labels = tmp_path / "labels.csv"
    write_labels(labels, {"not-a-candidate": "vulnerable"})
    with pytest.raises(ValueError, match="unknown candidates"):
        evaluation.run_metrics([root], [tmp_path], tmp_path / "out", labels)
    assert not (tmp_path / "out").exists()
    write_labels(labels, {"safe-1": "probably"})
    with pytest.raises(ValueError, match="Unknown label"):
        evaluation.read_labels(labels)
    with (root / "safe-1/code.py").open("a") as handle:
        handle.write("# changed\n")
    with pytest.raises(ValueError, match="hash mismatch"):
        evaluation.load_candidates([root])


def test_label_sheet_is_blind_and_merge_reports_agreement(tmp_path):
    root = experiment(tmp_path)
    sheet = tmp_path / "sheet.csv"
    assert evaluation.write_label_sheet([root], sheet) == 3
    with sheet.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert set(rows[0]) == {"candidate_id", "sample_id", "target_cwe", "code_file", "label", "notes"}
    assert all(r["label"] == "" for r in rows)
    with pytest.raises(FileExistsError):
        evaluation.write_label_sheet([root], sheet)

    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    write_labels(a, {"unsafe-1": "vulnerable", "unsafe-2": "vulnerable", "safe-1": "not_vulnerable"})
    write_labels(b, {"unsafe-1": "vulnerable", "unsafe-2": "uncertain", "safe-1": "not_vulnerable"})
    merged = tmp_path / "merged.csv"
    assert evaluation.merge_labels(a, b, merged) == {
        "pairs": 3, "agreed": 2, "agreement": 0.6667, "to_adjudicate": 1}
    labels, agreement = evaluation.read_labels(merged)
    assert labels["unsafe-2"] == "" and labels["unsafe-1"] == "vulnerable"
    assert agreement == {"pairs": 3, "agreed": 2, "agreement": 0.6667}


def test_merge_requires_complete_sheets_for_the_same_candidates(tmp_path):
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    write_labels(a, {"x": "vulnerable"})
    write_labels(b, {"x": ""})
    with pytest.raises(ValueError, match="not labeled by both"):
        evaluation.merge_labels(a, b, tmp_path / "m.csv")
    write_labels(b, {"y": "vulnerable"})
    with pytest.raises(ValueError, match="different candidates"):
        evaluation.merge_labels(a, b, tmp_path / "m.csv")
