"""Member 2: join static and dynamic results and compute detection metrics.

The evaluation unit is one candidate paired with its target CWE; see
docs/EVALUATION_PROTOCOL.md. There are no manual labels: a dynamic positive (an observed
security impact) is the reference, so static results are reported as confirmed or
unconfirmed by D. Detector results are joined by sample ID and code hash. Results are only
read here: candidate code is hashed, never imported or executed.
"""
import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from jsonschema.exceptions import ValidationError

from .contracts import utc_now, validate, write_json
from .generation import digest

THRESHOLDS = {"any": {"low", "medium", "high", "unknown"}, "medium": {"medium", "high"}}
CONFIGS = ("B0", "AST", "B1", "D", "P_union", "P_confirmed")
RESULT_TOOLS = {"bandit.json": "bandit", "ast.json": "ast", "pytest-docker.json": "pytest-docker"}
TABLE_COLUMNS = [
    "group", "candidate_id", "sample_id", "model", "run_index", "cwe", "code_sha256",
    "bandit_any", "bandit_medium", "ast_any", "ast_medium", "dynamic", "functional",
    "security_failed_tests", "bandit_seconds", "ast_seconds", "dynamic_seconds",
]
STATIC_CONFIGS = ("B0", "AST", "B1")
DISAGREEMENT_COLUMNS = ["threshold", "kind", "candidate_id", "sample_id", "model", "rule_ids",
                        "evidence", "security_failed_tests", "category", "notes"]


def load_candidates(paths: list[Path]) -> tuple[list[dict], list[dict]]:
    """Return (generated candidates, skipped records) from experiment or run directories."""
    candidates, skipped, seen = [], [], set()
    for path in paths:
        runs = [path] if (path / "generation.json").exists() else sorted(
            p for p in path.iterdir() if (p / "generation.json").exists()) if path.is_dir() else []
        if not runs:
            raise ValueError(f"No generation records found in {path}")
        for run in runs:
            record = json.loads((run / "generation.json").read_text(encoding="utf-8"))
            candidate_id = record.get("candidate_id") or run.name
            if candidate_id in seen:
                raise ValueError(f"Duplicate candidate ID: {candidate_id}")
            seen.add(candidate_id)
            if record.get("status") != "generated":
                skipped.append({"candidate_id": candidate_id, "sample_id": record.get("sample_id"),
                                "status": record.get("status")})
                continue
            code = run / record["code_file"]
            if digest(code.read_bytes()) != record["code_sha256"]:
                raise ValueError(f"Candidate hash mismatch: {candidate_id}")
            sample = json.loads((run / "sample.json").read_text(encoding="utf-8"))
            candidates.append({
                "group": path.name, "candidate_id": candidate_id, "sample_id": record["sample_id"],
                "model": record.get("requested_model"), "run_index": record.get("run_index", ""),
                "cwe": sample["cwe"], "code_sha256": record["code_sha256"], "code_file": str(code)})
    return candidates, skipped


def load_results(paths: list[Path]) -> tuple[dict, list[str]]:
    """Index analysis records by (sample_id, code_sha256, tool); report conflicting repeats."""
    results, warnings = {}, []
    for root in paths:
        files = [root] if root.is_file() else sorted(root.rglob("*.json"))
        for file in files:
            if file.name not in RESULT_TOOLS:
                continue
            record = json.loads(file.read_text(encoding="utf-8"))
            try:
                validate("analysis", record)
            except ValidationError as exc:
                raise ValueError(f"Invalid analysis record {file}: {exc.message}") from exc
            key = (record["sample_id"], record["code_sha256"], record["tool"])
            if key not in results:
                results[key] = record
            elif _fingerprint(results[key]) != _fingerprint(record):
                warnings.append(f"Conflicting {record['tool']} results for {key[0]} {key[1][:12]}; "
                                f"kept the first, ignored {file}")
    return results, warnings


def _fingerprint(record: dict) -> tuple:
    return (record["status"], sorted((f["rule_id"], f["line"] or 0) for f in record["findings"]),
            sorted((t["test_id"], t["outcome"]) for t in record["tests"]))


# Bandit files some checks under a broader CWE than the task's target. These rule IDs count
# as findings for the listed target CWE; the stored findings keep Bandit's own CWE.
EQUIVALENT_RULES = {
    "CWE-095": {"B307", "B102"},  # eval / exec, reported by Bandit as CWE-078
    "CWE-776": {"B313", "B314", "B315", "B316", "B317", "B318", "B319", "B320",  # XML parsers, reported as CWE-020
                "B405", "B406", "B407", "B408", "B409", "B410"},
}


def _counts_for(finding: dict, cwe: str, threshold: str) -> bool:
    """Whether a static finding counts as a detection of the target CWE at this threshold."""
    return ((finding["cwe"] == cwe or finding.get("rule_id") in EQUIVALENT_RULES.get(cwe, set()))
            and finding["severity"] in THRESHOLDS[threshold])


def _static_decision(record: dict | None, cwe: str, threshold: str) -> str:
    if record is None or record["status"] != "completed":
        return "inconclusive"
    return "yes" if any(_counts_for(f, cwe, threshold) for f in record["findings"]) else "no"


def _dynamic_decision(record: dict | None) -> tuple[str, str, list[str]]:
    """Return (security decision, functional outcome, failed security test IDs)."""
    if record is None:
        return "no_test", "no_test", []
    if record["status"] != "completed":
        return "inconclusive", "inconclusive", []
    security = [t for t in record["tests"] if t["category"] == "security"]
    functional = [t for t in record["tests"] if t["category"] == "functional"]
    failed = [t["test_id"] for t in security if t["outcome"] == "failed"]
    ran = [t for t in security if t["outcome"] == "passed"] or failed
    decision = "yes" if failed else "no" if ran else "inconclusive"
    if any(t["outcome"] == "failed" for t in functional):
        outcome = "failed"
    else:
        outcome = "passed" if any(t["outcome"] == "passed" for t in functional) else "inconclusive"
    return decision, outcome, failed


def _seconds(record: dict | None) -> str:
    if record is None or not record["started_at"] or not record["completed_at"]:
        return ""
    delta = datetime.fromisoformat(record["completed_at"]) - datetime.fromisoformat(record["started_at"])
    return f"{delta.total_seconds():.3f}"


def build_table(candidates: list[dict], results: dict) -> list[dict]:
    rows = []
    for candidate in candidates:
        key = (candidate["sample_id"], candidate["code_sha256"])
        bandit = results.get((*key, "bandit"))
        custom = results.get((*key, "ast"))
        dynamic = results.get((*key, "pytest-docker"))
        decision, functional, failed = _dynamic_decision(dynamic)
        row = {name: candidate[name] for name in (
            "group", "candidate_id", "sample_id", "model", "run_index", "cwe", "code_sha256")}
        for threshold in THRESHOLDS:
            row[f"bandit_{threshold}"] = _static_decision(bandit, candidate["cwe"], threshold)
            row[f"ast_{threshold}"] = _static_decision(custom, candidate["cwe"], threshold)
        row.update(dynamic=decision, functional=functional, security_failed_tests=";".join(failed),
                   bandit_seconds=_seconds(bandit), ast_seconds=_seconds(custom),
                   dynamic_seconds=_seconds(dynamic))
        rows.append(row)
    return rows


def _any_of(*values: str) -> str:
    return "yes" if "yes" in values else "no" if set(values) == {"no"} else "inconclusive"


def _all_of(*values: str) -> str:
    return "no" if "no" in values else "yes" if set(values) == {"yes"} else "inconclusive"


def decide(row: dict, threshold: str) -> dict:
    """Decision per configuration; an unavailable input yields inconclusive only if it matters."""
    bandit, custom = row[f"bandit_{threshold}"], row[f"ast_{threshold}"]
    static = _any_of(bandit, custom)
    dynamic = "inconclusive" if row["dynamic"] == "no_test" else row["dynamic"]
    return {"B0": bandit, "AST": custom, "B1": static, "D": dynamic,
            "P_union": _any_of(static, dynamic), "P_confirmed": _all_of(static, dynamic)}


def _ratio(top: int, bottom: int) -> float | None:
    return round(top / bottom, 4) if bottom else None


def reported(rows: list[dict], threshold: str, config: str) -> dict:
    """How many pairs a configuration reports, does not report, or cannot decide."""
    counts = Counter(decide(row, threshold)[config] for row in rows)
    return {"yes": counts["yes"], "no": counts["no"], "inconclusive": counts["inconclusive"]}


def agreement(rows: list[dict], threshold: str, first: str, second: str) -> dict:
    """Split pairs decided by both configurations: both, only first, only second, neither."""
    counts = Counter()
    for row in rows:
        decisions = decide(row, threshold)
        a, b = decisions[first], decisions[second]
        if "inconclusive" in (a, b):
            counts["undecided"] += 1
        else:
            counts["both" if a == b == "yes" else "neither" if a == b == "no" else
                   "first_only" if a == "yes" else "second_only"] += 1
    return {"first": first, "second": second,
            **{k: counts[k] for k in ("both", "first_only", "second_only", "neither", "undecided")}}


def versus_dynamic(rows: list[dict], threshold: str, config: str) -> dict:
    """A static configuration measured against D, the observed-impact reference."""
    split = agreement(rows, threshold, config, "D")
    both, static_only, dynamic_only = split["both"], split["first_only"], split["second_only"]
    return {**split, "unconfirmed_alerts": static_only,
            "confirmation_rate": _ratio(both, both + static_only),
            "coverage_of_confirmed": _ratio(both, both + dynamic_only)}


def summary(rows: list[dict], threshold: str) -> dict:
    return {"reported": {c: reported(rows, threshold, c) for c in CONFIGS},
            "vs_dynamic": {c: versus_dynamic(rows, threshold, c) for c in STATIC_CONFIGS},
            "bandit_vs_ast": agreement(rows, threshold, "B0", "AST")}


def _slices(rows: list[dict], name: str) -> dict:
    groups = {}
    for row in rows:
        groups.setdefault(str(row[name]), []).append(row)
    return groups


def _mean_seconds(rows: list[dict], column: str) -> float | None:
    values = [float(r[column]) for r in rows if r[column] != ""]
    return round(sum(values) / len(values), 3) if values else None


def compute_metrics(rows: list[dict]) -> dict:
    decided = [r for r in rows if r["dynamic"] in ("yes", "no")]
    metrics = {"pairs": len(rows), "distinct_code": len({r["code_sha256"] for r in rows}),
               "dynamic_coverage": {sample: dict(Counter(r["dynamic"] for r in group))
                                    for sample, group in _slices(rows, "sample_id").items()},
               "confirmed_share": _ratio(sum(r["dynamic"] == "yes" for r in decided), len(decided)),
               "functional_outcomes": dict(Counter(r["functional"] for r in rows)),
               "mean_seconds": {tool: _mean_seconds(rows, f"{tool}_seconds")
                                for tool in ("bandit", "ast", "dynamic")},
               "thresholds": {}}
    for threshold in THRESHOLDS:
        metrics["thresholds"][threshold] = {
            "overall": summary(rows, threshold),
            "by_task": {k: summary(v, threshold) for k, v in _slices(rows, "sample_id").items()},
            "by_model": {k: summary(v, threshold) for k, v in _slices(rows, "model").items()},
        }
    return metrics


def disagreement_rows(rows: list[dict], results: dict) -> list[dict]:
    """Pairs where B1 and D disagree, with the static evidence and failed security tests."""
    output = []
    for row in rows:
        for threshold in THRESHOLDS:
            decisions = decide(row, threshold)
            kind = {("yes", "no"): "static_only", ("no", "yes"): "dynamic_only"}.get(
                (decisions["B1"], decisions["D"]))
            if kind is None:
                continue
            findings = [f for tool in ("bandit", "ast")
                        for f in (results.get((row["sample_id"], row["code_sha256"], tool)) or {}).get("findings", [])
                        if _counts_for(f, row["cwe"], threshold)]
            output.append({"threshold": threshold, "kind": kind, "candidate_id": row["candidate_id"],
                           "sample_id": row["sample_id"], "model": row["model"],
                           "rule_ids": ";".join(f["rule_id"] for f in findings),
                           "evidence": " | ".join(f["evidence"] for f in findings)[:1000],
                           "security_failed_tests": row["security_failed_tests"],
                           "category": "", "notes": ""})
    return output


def _value(value) -> str:
    return "n/a" if value is None else str(value)


def format_report(metrics: dict, skipped: list[dict], warnings: list[str]) -> str:
    lines = ["# Detection evaluation report", "",
             f"Generated {utc_now()}. Unit: one (candidate, target CWE) pair. Pairs: {metrics['pairs']} "
             f"({metrics['distinct_code']} distinct code files). Share of dynamically decided pairs with "
             f"a confirmed vulnerability (D positive): {_value(metrics['confirmed_share'])}.", "",
             "There are no manual labels. D (an observed security impact) is the reference: a static "
             "alert without a D positive is unconfirmed, not a proven false positive, and a "
             "vulnerability neither approach reports is not counted. `n/a` means the denominator is zero.", ""]
    for threshold, data in metrics["thresholds"].items():
        overall = data["overall"]
        lines += [f"## Static threshold: {threshold}", "",
                  "| Config | Reported | Not reported | Undecided |", "|---|---|---|---|"]
        for config, r in overall["reported"].items():
            lines.append(f"| {config} | {r['yes']} | {r['no']} | {r['inconclusive']} |")
        lines += ["", "| Static vs. D | Both | Static only (unconfirmed) | D only | Neither | Undecided "
                      "| Confirmation rate | Coverage of confirmed |", "|---|---|---|---|---|---|---|---|"]
        for config, v in overall["vs_dynamic"].items():
            lines.append(f"| {config} | {v['both']} | {v['first_only']} | {v['second_only']} | {v['neither']} "
                         f"| {v['undecided']} | {_value(v['confirmation_rate'])} "
                         f"| {_value(v['coverage_of_confirmed'])} |")
        a = overall["bandit_vs_ast"]
        lines += ["", f"Bandit vs. AST: both {a['both']}, Bandit only {a['first_only']}, "
                      f"AST only {a['second_only']}, neither {a['neither']}, undecided {a['undecided']}.", ""]
    lines += ["## Coverage and quality", "", f"- Dynamic outcomes by task: {metrics['dynamic_coverage']}",
              f"- Functional outcomes: {metrics['functional_outcomes']}",
              f"- Mean analysis seconds: {metrics['mean_seconds']}",
              f"- Candidates skipped (not generated): {len(skipped)}"]
    lines += [f"- Warning: {w}" for w in warnings]
    return "\n".join(lines) + "\n"


def _write_csv(path: Path, columns: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def run_metrics(candidate_paths: list[Path], result_paths: list[Path], out: Path) -> dict:
    candidates, skipped = load_candidates(candidate_paths)
    results, warnings = load_results(result_paths)
    rows = build_table(candidates, results)
    metrics = compute_metrics(rows)
    metrics.update(skipped=skipped, warnings=warnings)
    out.mkdir(parents=True, exist_ok=False)
    _write_csv(out / "evaluation_table.csv", TABLE_COLUMNS, rows)
    _write_csv(out / "disagreements.csv", DISAGREEMENT_COLUMNS, disagreement_rows(rows, results))
    write_json(out / "metrics.json", metrics)
    (out / "report.md").write_text(format_report(metrics, skipped, warnings), encoding="utf-8")
    return metrics
