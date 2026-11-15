"""Member 3: run the Docker functional/security tests over generation run directories.

Writes, under a new output directory:
  <candidate>/pytest-docker.json     analysis contract (shared schema), read by `metrics`
  <candidate>/pytest-docker/         raw evidence: report, stdout/stderr, commands, environment
  dynamic_summary.json / .md / .csv  per-candidate D decisions and aggregate counts

D decision (configuration D of the experiment plan), per candidate and target CWE:
  yes           at least one `security` test failed; these tests fail only on an observed
                security impact, never on a candidate exception or a rejected input
  no            security tests ran and none failed
  inconclusive  the run did not complete (timeout, import error, Docker or harness failure)
Candidates are executed only inside the container and are never modified.
"""
import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from jsonschema.exceptions import ValidationError

from .analyzers.dynamic import DockerPytestAnalyzer
from .contracts import utc_now, validate, write_json
from .pipeline import load_candidate

SUMMARY_VERSION = "dynamic-summary-0.1"
IMPACT_MARKER = "SECURITY IMPACT"
COLUMNS = ["candidate_id", "sample_id", "cwe", "model", "run_index", "code_sha256", "status",
           "d_decision", "functional", "security_passed", "security_failed", "functional_passed",
           "functional_failed", "failed_security_tests", "failed_functional_tests", "seconds", "error"]


def collect_runs(paths: list[Path]) -> list[Path]:
    runs = []
    for path in paths:
        if (path / "generation.json").is_file():
            runs.append(path)
        elif path.is_dir():
            found = sorted(p for p in path.iterdir() if (p / "generation.json").is_file())
            if not found:
                raise ValueError(f"No generation records found in {path}")
            runs.extend(found)
        else:
            raise ValueError(f"Not a generation run or experiment directory: {path}")
    names = Counter(run.name for run in runs)
    duplicates = sorted(name for name, count in names.items() if count > 1)
    if duplicates:
        raise ValueError(f"Duplicate candidate directory name: {duplicates[0]}")
    return runs


def _manifest_hashes(run: Path) -> dict:
    """Code hashes recorded in the frozen experiment manifest next to the run, if any."""
    manifest = run.parent / "manifest.json"
    if not manifest.is_file():
        return {}
    results = json.loads(manifest.read_text(encoding="utf-8")).get("results", [])
    return {r["candidate_id"]: r.get("code_sha256") for r in results if "candidate_id" in r}


def decide(record: dict) -> dict:
    """Reduce one pytest-docker analysis record to the D decision and test counts."""
    tests = {c: [t for t in record["tests"] if t["category"] == c] for c in ("security", "functional")}
    failed = {c: [t["test_id"] for t in tests[c] if t["outcome"] == "failed"] for c in tests}
    passed = {c: sum(t["outcome"] == "passed" for t in tests[c]) for c in tests}
    if record["status"] != "completed":
        decision = functional = "inconclusive"
    else:
        decision = "yes" if failed["security"] else "no" if passed["security"] else "inconclusive"
        functional = "failed" if failed["functional"] else "passed" if passed["functional"] else "inconclusive"
    unexplained = [t["test_id"] for t in tests["security"]
                   if t["outcome"] == "failed" and IMPACT_MARKER not in t["message"]]
    return {"d_decision": decision, "functional": functional,
            "security_passed": passed["security"], "security_failed": len(failed["security"]),
            "functional_passed": passed["functional"], "functional_failed": len(failed["functional"]),
            "failed_security_tests": failed["security"], "failed_functional_tests": failed["functional"],
            "unexplained_security_failures": unexplained}


def _seconds(record: dict) -> float | None:
    if not record["started_at"] or not record["completed_at"]:
        return None
    delta = datetime.fromisoformat(record["completed_at"]) - datetime.fromisoformat(record["started_at"])
    return round(delta.total_seconds(), 3)


def _share(count: int, total: int) -> str:
    return f"{count}/{total} ({100 * count / total:.1f}%)" if total else "0/0 (n/a)"


def aggregate(rows: list[dict]) -> dict:
    """Counts over evaluated candidates; rates use completed runs as the denominator."""
    done = [r for r in rows if r["status"] == "completed"]
    seconds = [r["seconds"] for r in rows if r["seconds"] is not None]
    counts = {
        "candidates": len(rows), "completed": len(done), "inconclusive": len(rows) - len(done),
        "d_yes": sum(r["d_decision"] == "yes" for r in done),
        "d_no": sum(r["d_decision"] == "no" for r in done),
        "security_tests_passed": sum(r["d_decision"] == "no" for r in done),
        "functional_tests_passed": sum(r["functional"] == "passed" for r in done),
        "mean_seconds": round(sum(seconds) / len(seconds), 3) if seconds else None,
        "total_seconds": round(sum(seconds), 3),
    }
    for name in ("d_yes", "security_tests_passed", "functional_tests_passed"):
        counts[name + "_share"] = _share(counts[name], len(done))
    return counts


def _groups(rows: list[dict], *keys: str) -> dict:
    groups = {}
    for row in rows:
        groups.setdefault(" / ".join(str(row[k]) for k in keys), []).append(row)
    return {name: aggregate(group) for name, group in sorted(groups.items())}


def run_dynamic(paths: list[Path], out: Path, image: str = "security-eval-tests:dev",
                timeout: int = 60, analyzer_factory=DockerPytestAnalyzer, progress=None) -> dict:
    runs = collect_runs(paths)
    out.mkdir(parents=True, exist_ok=False)
    rows, skipped, environments = [], [], Counter()
    for run in runs:
        generation = json.loads((run / "generation.json").read_text(encoding="utf-8"))
        candidate_id = generation.get("candidate_id") or run.name
        try:
            code, sample, run_id = load_candidate(run)
            expected = _manifest_hashes(run).get(candidate_id)
            if expected and expected != generation["code_sha256"]:
                raise ValueError("Candidate hash differs from the experiment manifest")
        except (ValueError, OSError, ValidationError, TypeError, KeyError) as exc:
            skipped.append({"candidate_id": candidate_id, "sample_id": generation.get("sample_id"),
                            "generation_status": generation.get("status"), "reason": str(exc)})
            if progress:
                progress(f"{candidate_id}: skipped ({exc})")
            continue
        target = out / run.name
        record = analyzer_factory(evidence_dir=target / "pytest-docker", image=image,
                                  timeout=timeout).analyze(code, sample, run_id)
        validate("analysis", record)
        write_json(target / "pytest-docker.json", record)
        environment = target / "pytest-docker" / "environment.json"
        report = target / "pytest-docker" / "report.json"
        image_id = json.loads(environment.read_text()).get("image_id") if environment.is_file() else None
        tests_hash = json.dumps(json.loads(report.read_text()).get("test_sha256"), sort_keys=True) \
            if report.is_file() else None
        environments[(image_id, tests_hash)] += 1
        row = {"candidate_id": candidate_id, "sample_id": sample["sample_id"], "cwe": sample["cwe"],
               "model": generation.get("requested_model") or generation.get("model"),
               "run_index": generation.get("run_index"), "code_sha256": record["code_sha256"],
               "status": record["status"], **decide(record), "seconds": _seconds(record),
               "error": record["error"], "record": f"{run.name}/pytest-docker.json"}
        rows.append(row)
        if progress:
            progress(f"{candidate_id}: {record['status']} D={row['d_decision']} functional={row['functional']}"
                     + (f" error={record['error']['message'][:120]}" if record["error"] else ""))
    by_code = {}
    for row in rows:
        signature = (row["status"], tuple(row["failed_security_tests"]), tuple(row["failed_functional_tests"]))
        by_code.setdefault((row["sample_id"], row["code_sha256"]), {}).setdefault(signature, []).append(row["candidate_id"])
    summary = {
        "summary_version": SUMMARY_VERSION, "generated_at": utc_now(),
        "requested_image": image, "timeout_seconds": timeout,
        "decision_rule": "D is 'yes' when at least one security test failed. Security tests fail only "
                         "on an observed security impact; exceptions, timeouts and harness or Docker "
                         "errors are never detections. D is supporting evidence, not ground truth.",
        "environments": [{"image_id": k[0], "test_sha256": json.loads(k[1]) if k[1] else None, "candidates": n}
                         for k, n in environments.items()],
        "overall": aggregate(rows), "by_task": _groups(rows, "sample_id"),
        "by_model": _groups(rows, "model"), "by_task_and_model": _groups(rows, "sample_id", "model"),
        "identical_code_with_different_outcomes": [
            {"sample_id": key[0], "code_sha256": key[1], "candidates": sorted(sum(v.values(), []))}
            for key, v in by_code.items() if len(v) > 1],
        "unexplained_security_failures": [
            {"candidate_id": r["candidate_id"], "tests": r["unexplained_security_failures"]}
            for r in rows if r["unexplained_security_failures"]],
        "skipped": skipped, "candidates": rows,
    }
    write_json(out / "dynamic_summary.json", summary)
    with (out / "dynamic_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, "failed_security_tests": ";".join(row["failed_security_tests"]),
                             "failed_functional_tests": ";".join(row["failed_functional_tests"]),
                             "error": row["error"]["message"] if row["error"] else ""})
    (out / "dynamic_summary.md").write_text(format_summary(summary), encoding="utf-8")
    return summary


def format_summary(summary: dict) -> str:
    lines = ["# Dynamic testing summary (configuration D)", "",
             f"Generated {summary['generated_at']}. {summary['decision_rule']}", "",
             "Rates use completed runs as the denominator; inconclusive runs are listed separately.", "",
             "| Slice | Candidates | Completed | Inconclusive | D positive | Security tests passed "
             "| Functional tests passed | Mean seconds |", "|---|---|---|---|---|---|---|---|"]
    slices = [("Overall", summary["overall"])]
    for name in ("by_task", "by_model", "by_task_and_model"):
        slices += list(summary[name].items())
    for name, a in slices:
        lines.append(f"| {name} | {a['candidates']} | {a['completed']} | {a['inconclusive']} | {a['d_yes_share']} "
                     f"| {a['security_tests_passed_share']} | {a['functional_tests_passed_share']} "
                     f"| {a['mean_seconds'] if a['mean_seconds'] is not None else 'n/a'} |")
    positives = [r for r in summary["candidates"] if r["d_decision"] == "yes"]
    lines += ["", f"## D-positive candidates ({len(positives)})", ""]
    lines += [f"- `{r['candidate_id']}`: {', '.join(t.split('::')[-1] for t in r['failed_security_tests'])}"
              for r in positives] or ["None."]
    errors = [r for r in summary["candidates"] if r["status"] != "completed"]
    lines += ["", f"## Inconclusive runs ({len(errors)})", ""]
    lines += [f"- `{r['candidate_id']}`: {r['error']['message'][:200] if r['error'] else r['status']}"
              for r in errors] or ["None."]
    lines += ["", f"## Skipped inputs ({len(summary['skipped'])})", ""]
    lines += [f"- `{s['candidate_id']}`: {s['reason']}" for s in summary["skipped"]] or ["None."]
    for title, key in (("Identical code with different outcomes", "identical_code_with_different_outcomes"),
                       ("Security failures without an impact message (review the harness)",
                        "unexplained_security_failures")):
        lines += ["", f"## {title} ({len(summary[key])})", ""]
        lines += [f"- {json.dumps(item)}" for item in summary[key]] or ["None."]
    return "\n".join(lines) + "\n"


def all_completed(summary: dict) -> bool:
    return bool(summary["candidates"]) and not summary["skipped"] and all(
        r["status"] == "completed" for r in summary["candidates"])
