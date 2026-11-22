"""Batch runner checks with a synthetic analyzer; no Docker and no candidate execution."""
import json

import pytest

from security_eval.analyzers.base import pending
from security_eval.contracts import load_samples, utc_now, validate, write_json
from security_eval.dynamic_runner import all_completed, collect_runs, decide, run_dynamic
from security_eval.generation import generate, prepare
from test_contracts import SAMPLES
from test_generation import fixture_client

IMPACT = "SECURITY IMPACT (CWE-089): synthetic"


def record(tests, status="completed"):
    return {"status": status, "tests": [
        {"test_id": f"t{i}", "category": c, "outcome": o, "message": m} for i, (c, o, m) in enumerate(tests)]}


def test_decision_rule():
    clean = decide(record([("security", "passed", ""), ("functional", "passed", "")]))
    assert (clean["d_decision"], clean["functional"]) == ("no", "passed")
    hit = decide(record([("security", "failed", IMPACT), ("security", "passed", ""), ("functional", "passed", "")]))
    assert (hit["d_decision"], hit["failed_security_tests"], hit["unexplained_security_failures"]) == ("yes", ["t0"], [])
    # A functional failure is never a detection.
    broken = decide(record([("security", "passed", ""), ("functional", "failed", "AssertionError")]))
    assert (broken["d_decision"], broken["functional"]) == ("no", "failed")
    # Errors and runs without an executed security test are inconclusive, not negative.
    assert decide(record([], "error"))["d_decision"] == "inconclusive"
    assert decide(record([("security", "skipped", ""), ("functional", "passed", "")]))["d_decision"] == "inconclusive"
    assert decide(record([("security", "failed", "RuntimeError")]))["unexplained_security_failures"] == ["t0"]


def test_hardening_is_reported_but_never_changes_d_or_functional():
    tests = record([("security", "passed", ""), ("functional", "passed", "")])
    checks = [{"test_id": "h0", "category": "hardening", "outcome": "failed", "message": ""},
              {"test_id": "h1", "category": "hardening", "outcome": "passed", "message": ""}]
    result = decide(tests, checks)
    assert (result["d_decision"], result["functional"]) == ("no", "passed")
    assert (result["hardening"], result["hardening_passed"], result["failed_hardening_tests"]) == ("failed", 1, ["h0"])
    assert decide(tests, checks[1:])["hardening"] == "passed"
    assert decide(tests)["hardening"] == "none"
    assert decide(record([], "error"), checks)["hardening"] == "none"


def fake_analyzer(outcomes):
    """Analyzer factory returning synthetic records keyed by a substring of the candidate code."""
    class Fake:
        def __init__(self, evidence_dir, image, timeout):
            self.evidence_dir = evidence_dir

        def analyze(self, code_path, sample, run_id):
            result = pending(code_path, sample, run_id, "pytest-docker")
            kind = next(k for k in outcomes if k in code_path.read_text())
            self.evidence_dir.mkdir(parents=True)
            write_json(self.evidence_dir / "environment.json", {"image_id": "sha256:fixture"})
            if outcomes[kind] is None:
                result.update(status="error", started_at=utc_now(),
                              error={"type": "RunnerError", "message": "Timeout: synthetic"})
                return result
            write_json(self.evidence_dir / "report.json", {"test_sha256": {"t.py": "0" * 64}, "hardening_tests": [
                {"test_id": "hard", "category": "hardening", "outcome": "failed", "message": ""}]})
            result.update(status="completed", tool_version="pytest fixture", started_at=utc_now(),
                          evidence_files=["pytest-docker/report.json"], tests=[
                              {"test_id": "sec", "category": "security", "outcome": outcomes[kind], "message":
                               IMPACT if outcomes[kind] == "failed" else ""},
                              {"test_id": "fun", "category": "functional", "outcome": "passed", "message": ""}])
            return result
    return Fake


def test_batch_writes_contracts_and_summary(tmp_path):
    sample = load_samples(SAMPLES)[0]
    experiment = tmp_path / "experiment"
    for name in ("safe", "unsafe", "hang"):
        generate(sample, experiment / name, "fixture-only",
                 client=fixture_client(f"def remove_user(conn, username):\n    return 0  # {name}\n"))
    prepare(sample, experiment / "prepared_only", "fixture-only")
    out = tmp_path / "dynamic"
    lines = []
    summary = run_dynamic([experiment], out, progress=lines.append,
                          analyzer_factory=fake_analyzer({"unsafe": "failed", "hang": None, "safe": "passed"}))
    rows = {r["record"].split("/")[0]: r for r in summary["candidates"]}
    assert {k: v["d_decision"] for k, v in rows.items()} == {"safe": "no", "unsafe": "yes", "hang": "inconclusive"}
    assert summary["overall"]["d_yes_share"] == "1/2 (50.0%)"
    assert summary["overall"]["inconclusive"] == 1 and len(lines) == 4
    assert summary["overall"]["hardening_all_passed_share"] == "0/2 (0.0%)"
    assert summary["overall"]["distinct_d_yes_share"] == "1/2 (50.0%)"
    assert summary["overall"]["tasks_with_d_yes_share"] == "1/1 (100.0%)"
    assert rows["safe"]["functional"] == "passed" and rows["safe"]["failed_hardening_tests"] == ["hard"]
    assert [s["generation_status"] for s in summary["skipped"]] == ["prepared"]
    assert not all_completed(summary)
    for name in rows:
        validate("analysis", json.loads((out / name / "pytest-docker.json").read_text()))
    assert "## D-positive candidates (1)" in (out / "dynamic_summary.md").read_text()
    assert (out / "dynamic_summary.csv").read_text().count("\n") == 4
    with pytest.raises(FileExistsError):
        run_dynamic([experiment], out, analyzer_factory=fake_analyzer({"": "passed"}))


def test_manifest_mismatch_and_tampering_are_skipped(tmp_path):
    sample = load_samples(SAMPLES)[0]
    experiment = tmp_path / "experiment"
    for name in ("a", "b"):
        generate(sample, experiment / name, "fixture-only",
                 client=fixture_client(f"def remove_user(conn, username):\n    return 0  # {name}\n"))
    identifier = json.loads((experiment / "a/generation.json").read_text()).get("candidate_id") or "a"
    write_json(experiment / "manifest.json", {"results": [{"candidate_id": identifier, "code_sha256": "0" * 64}]})
    (experiment / "b/code.py").write_text("changed")
    summary = run_dynamic([experiment], tmp_path / "out", analyzer_factory=fake_analyzer({"": "passed"}))
    assert summary["candidates"] == []
    assert sorted("manifest" in s["reason"] or "hash mismatch" in s["reason"] for s in summary["skipped"]) == [True, True]
    assert not all_completed(summary)
    with pytest.raises(ValueError):
        collect_runs([tmp_path / "missing"])
