"""Synthetic fixtures validate the repair harness, never repair performance."""

import json
from types import SimpleNamespace

from security_eval.repair import feedback, report, run_repair, select

SHA = "a" * 64
FIXED = "def f():\n    return 1\n"


def _record(tool, sha, findings=(), tests=()):
    return {"sample_id": "s", "code_sha256": sha, "tool": tool, "status": "completed",
            "findings": list(findings), "tests": list(tests)}


def _results(sha=SHA, outcome="failed"):
    finding = {"rule_id": "B1", "cwe": "CWE-1", "severity": "low", "line": 2, "message": "m"}
    tests = [{"test_id": "t.py::test_sec[x]", "category": "security", "outcome": outcome,
              "message": "def test():\nE   AssertionError: IMPACT x\nE   assert 0"},
             {"test_id": "t.py::test_fn", "category": "functional", "outcome": "passed", "message": ""}]
    return {("s", sha, "bandit"): _record("bandit", sha, [finding]),
            ("s", sha, "pytest-docker"): _record("pytest-docker", sha, tests=tests)}


def _candidate(run, sha=SHA):
    return {"candidate_id": f"s__m__run_{run:02d}", "sample_id": "s", "model": "m",
            "run_index": run, "code_sha256": sha}


def test_select_takes_lowest_positive_run_per_task_and_model():
    clean = "b" * 64
    results = {**_results(), **_results(clean, "passed")}
    chosen = select([_candidate(3), _candidate(2), _candidate(1, clean)], results)
    assert [c["run_index"] for c in chosen] == [2]


def test_only_r2_feedback_names_failed_tests():
    zero, first, second = (feedback(_candidate(1), _results(), c) for c in ("R0", "R1", "R2"))
    assert "B1" not in zero and "test_sec" not in zero
    assert "B1" in first and "test_sec" not in first
    assert second.startswith(first) and "- test_sec[x]: AssertionError: IMPACT x" in second


def test_repair_writes_ordinary_run_directories_and_report(tmp_path, monkeypatch):
    from security_eval import repair
    from security_eval.contracts import load_samples
    from pathlib import Path
    sample = load_samples(Path(__file__).resolve().parents[2] / "data/samples.jsonl")[0]
    source = tmp_path / "src" / "c1"
    source.mkdir(parents=True)
    (source / "code.py").write_text("ORIGINAL_CODE = 1\n")
    (source / "sample.json").write_text(json.dumps(sample))
    candidate = dict(_candidate(1), sample_id=sample["sample_id"], code_file=str(source / "code.py"))
    results = {(sample["sample_id"], *key[1:]): dict(value, sample_id=sample["sample_id"])
               for key, value in _results().items()}
    monkeypatch.setattr(repair, "load_candidates", lambda paths: ([candidate], []))
    monkeypatch.setattr(repair, "load_results", lambda paths: (results, []))
    code = f"def {sample['entry_point']}(*args):\n    return None\n"
    raw = {"id": "msg_fixture", "model": "fixture-only", "stop_reason": "end_turn",
           "content": [{"type": "text", "text": code}], "usage": {"input_tokens": 1, "output_tokens": 1}}
    seen = []
    client = SimpleNamespace(messages=SimpleNamespace(
        create=lambda **request: seen.append(request) or SimpleNamespace(model_dump=lambda **kw: raw)))
    manifest = run_repair([tmp_path], [tmp_path], tmp_path / "out", "fixture-model", client=client,
                          conditions=("R1", "R2"))
    assert [e["status"] for e in manifest["repairs"]] == ["generated", "generated"]
    assert "ORIGINAL_CODE" in seen[0]["messages"][0]["content"]
    assert "Failed security tests" in seen[1]["messages"][0]["content"]
    assert (tmp_path / "out" / "s__m__run_01__repair_r2" / "code.py").read_text() == code
    fixed = manifest["repairs"][0]["code_sha256"]
    results.update({(sample["sample_id"], *key[1:]): value for key, value in _results(fixed, "passed").items()})
    summary = report([tmp_path / "out"], [tmp_path], tmp_path / "report")
    assert summary["R1"] == {"attempts": 1, "repaired": 1, "security_passed": 1,
                             "functional_broken": 0, "not_tested": 0}
