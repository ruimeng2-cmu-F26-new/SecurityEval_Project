"""Member 2: join detector results with manual labels and compute detection metrics.

The evaluation unit is one candidate paired with its target CWE; see
docs/EVALUATION_PROTOCOL.md. Detector results are joined by sample ID and code hash.
Results are only read here: candidate code is hashed, never imported or executed.
"""
import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from jsonschema.exceptions import ValidationError

from .contracts import utc_now, validate, write_json
from .generation import digest

LABELS = ("vulnerable", "not_vulnerable", "uncertain")
THRESHOLDS = {"any": {"low", "medium", "high", "unknown"}, "medium": {"medium", "high"}}
CONFIGS = ("B0", "AST", "B1", "D", "P_union", "P_confirmed")
RESULT_TOOLS = {"bandit.json": "bandit", "ast.json": "ast", "pytest-docker.json": "pytest-docker"}
TABLE_COLUMNS = [
    "group", "candidate_id", "sample_id", "model", "run_index", "cwe", "code_sha256",
    "bandit_any", "bandit_medium", "ast_any", "ast_medium", "dynamic", "functional",
    "security_failed_tests", "label", "bandit_seconds", "ast_seconds", "dynamic_seconds",
]
SHEET_COLUMNS = ["candidate_id", "sample_id", "target_cwe", "code_file", "label", "notes"]
MERGED_COLUMNS = ["candidate_id", "reviewer_a", "reviewer_b", "label", "adjudication_note"]
ERROR_COLUMNS = ["threshold", "kind", "candidate_id", "sample_id", "model", "label",
                 "rule_ids", "evidence", "category", "notes"]


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


def _static_decision(record: dict | None, cwe: str, threshold: str) -> str:
    if record is None or record["status"] != "completed":
        return "inconclusive"
    return "yes" if any(f["cwe"] == cwe and f["severity"] in THRESHOLDS[threshold]
                        for f in record["findings"]) else "no"


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


def build_table(candidates: list[dict], results: dict, labels: dict | None = None) -> list[dict]:
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
                   label=(labels or {}).get(candidate["candidate_id"]) or "unlabeled",
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


def score(rows: list[dict], threshold: str, config: str) -> dict:
    counts = Counter()
    for row in rows:
        if row["label"] not in ("vulnerable", "not_vulnerable"):
            counts["unlabeled_or_uncertain"] += 1
            continue
        decision = decide(row, threshold)[config]
        if decision == "inconclusive":
            counts["inconclusive"] += 1
        else:
            positive, vulnerable = decision == "yes", row["label"] == "vulnerable"
            counts[("tp" if vulnerable else "fp") if positive else ("fn" if vulnerable else "tn")] += 1
    tp, fp, fn, tn = (counts[k] for k in ("tp", "fp", "fn", "tn"))
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "evaluated": tp + fp + fn + tn,
            "precision": _ratio(tp, tp + fp), "recall": _ratio(tp, tp + fn),
            "f1": _ratio(2 * tp, 2 * tp + fp + fn),
            "false_positive_rate": _ratio(fp, fp + tn),
            "inconclusive": counts["inconclusive"],
            "unlabeled_or_uncertain": counts["unlabeled_or_uncertain"]}


def overlap(rows: list[dict], threshold: str, first: str, second: str) -> dict:
    """Split labeled pairs decided by both configurations: only first, only second, both, neither."""
    result = {label: {"first_only": 0, "second_only": 0, "both": 0, "neither": 0}
              for label in ("vulnerable", "not_vulnerable")}
    for row in rows:
        decisions = decide(row, threshold)
        a, b = decisions[first], decisions[second]
        if row["label"] in result and "inconclusive" not in (a, b):
            name = "both" if a == b == "yes" else "neither" if a == b == "no" else (
                "first_only" if a == "yes" else "second_only")
            result[row["label"]][name] += 1
    return {"first": first, "second": second, **result}


def compare(rows: list[dict], threshold: str, base: str, other: str) -> dict:
    """Compare two configurations on the same rows, so that the differences are paired."""
    paired = [r for r in rows if decide(r, threshold)[base] != "inconclusive"
              and decide(r, threshold)[other] != "inconclusive"]
    before, after = score(paired, threshold, base), score(paired, threshold, other)

    def change(name):
        if before[name] is None or after[name] is None:
            return None
        return round(after[name] - before[name], 4)

    return {"base": base, "other": other, "paired_rows": before["evaluated"],
            "tp_change": after["tp"] - before["tp"], "fp_change": after["fp"] - before["fp"],
            "precision_change": change("precision"), "recall_change": change("recall")}


def _slices(rows: list[dict], name: str) -> dict:
    groups = {}
    for row in rows:
        groups.setdefault(str(row[name]), []).append(row)
    return groups


def _mean_seconds(rows: list[dict], column: str) -> float | None:
    values = [float(r[column]) for r in rows if r[column] != ""]
    return round(sum(values) / len(values), 3) if values else None


def compute_metrics(rows: list[dict]) -> dict:
    metrics = {"pairs": len(rows), "distinct_code": len({r["code_sha256"] for r in rows}),
               "labels": dict(Counter(r["label"] for r in rows)),
               "dynamic_coverage": {sample: dict(Counter(r["dynamic"] for r in group))
                                    for sample, group in _slices(rows, "sample_id").items()},
               "functional_outcomes": dict(Counter(r["functional"] for r in rows)),
               "mean_seconds": {tool: _mean_seconds(rows, f"{tool}_seconds")
                                for tool in ("bandit", "ast", "dynamic")},
               "thresholds": {}}
    labeled = [r for r in rows if r["label"] in ("vulnerable", "not_vulnerable")]
    metrics["vulnerability_rate"] = _ratio(sum(r["label"] == "vulnerable" for r in labeled), len(labeled))
    for threshold in THRESHOLDS:
        metrics["thresholds"][threshold] = {
            "overall": {c: score(rows, threshold, c) for c in CONFIGS},
            "by_task": {k: {c: score(v, threshold, c) for c in CONFIGS}
                        for k, v in _slices(rows, "sample_id").items()},
            "by_model": {k: {c: score(v, threshold, c) for c in CONFIGS}
                         for k, v in _slices(rows, "model").items()},
            "overlap": {"static_vs_dynamic": overlap(rows, threshold, "B1", "D"),
                        "bandit_vs_ast": overlap(rows, threshold, "B0", "AST")},
            "fusion": {"ast_added_to_bandit": compare(rows, threshold, "B0", "B1"),
                       "union_vs_static": compare(rows, threshold, "B1", "P_union"),
                       "confirmed_vs_static": compare(rows, threshold, "B1", "P_confirmed")},
        }
    return metrics


def error_rows(rows: list[dict], results: dict) -> list[dict]:
    """Static (B1) false positives and false negatives, for manual error analysis."""
    output = []
    for row in rows:
        for threshold in THRESHOLDS:
            decision = decide(row, threshold)["B1"]
            kind = {("yes", "not_vulnerable"): "false_positive",
                    ("no", "vulnerable"): "false_negative"}.get((decision, row["label"]))
            if kind is None:
                continue
            findings = [f for tool in ("bandit", "ast")
                        for f in (results.get((row["sample_id"], row["code_sha256"], tool)) or {}).get("findings", [])
                        if f["cwe"] == row["cwe"] and f["severity"] in THRESHOLDS[threshold]]
            output.append({"threshold": threshold, "kind": kind, "candidate_id": row["candidate_id"],
                           "sample_id": row["sample_id"], "model": row["model"], "label": row["label"],
                           "rule_ids": ";".join(f["rule_id"] for f in findings),
                           "evidence": " | ".join(f["evidence"] for f in findings)[:1000],
                           "category": "", "notes": ""})
    return output


def _value(value) -> str:
    return "n/a" if value is None else str(value)


def format_report(metrics: dict, skipped: list[dict], warnings: list[str], agreement: dict | None) -> str:
    labels = metrics["labels"]
    lines = ["# Detection evaluation report", "",
             f"Generated {utc_now()}. Unit: one (candidate, target CWE) pair. Pairs: {metrics['pairs']} "
             f"({metrics['distinct_code']} distinct code files). Labels: {labels}. "
             f"Vulnerability rate among labeled pairs: {_value(metrics['vulnerability_rate'])}.", "",
             "P_union cannot have lower recall than B1 by construction, so read its recall gain "
             "together with the false-positive change. Results are descriptive; `n/a` means the "
             "denominator is zero.", ""]
    if not metrics["labels"].get("vulnerable"):
        lines += ["**No pair is labeled vulnerable, so recall and false negatives cannot be evaluated.**", ""]
    if agreement:
        lines += [f"First-pass reviewer agreement: {agreement['agreed']}/{agreement['pairs']} "
                  f"({_value(agreement['agreement'])}).", ""]
    for threshold, data in metrics["thresholds"].items():
        lines += [f"## Static threshold: {threshold}", "",
                  "| Config | TP | FP | FN | TN | Precision | Recall | F1 | FPR | Inconclusive |",
                  "|---|---|---|---|---|---|---|---|---|---|"]
        for config, s in data["overall"].items():
            lines.append(f"| {config} | {s['tp']} | {s['fp']} | {s['fn']} | {s['tn']} | {_value(s['precision'])} "
                         f"| {_value(s['recall'])} | {_value(s['f1'])} | {_value(s['false_positive_rate'])} "
                         f"| {s['inconclusive']} |")
        lines += ["", "| Overlap | Label | First only | Second only | Both | Neither |", "|---|---|---|---|---|---|"]
        for item in data["overlap"].values():
            for label in ("vulnerable", "not_vulnerable"):
                o = item[label]
                lines.append(f"| {item['first']} vs. {item['second']} | {label} | {o['first_only']} "
                             f"| {o['second_only']} | {o['both']} | {o['neither']} |")
        lines += ["", "| Paired change | Rows | TP change | FP change | Precision change | Recall change |",
                  "|---|---|---|---|---|---|"]
        for item in data["fusion"].values():
            lines.append(f"| {item['base']} to {item['other']} | {item['paired_rows']} | {item['tp_change']} "
                         f"| {item['fp_change']} | {_value(item['precision_change'])} "
                         f"| {_value(item['recall_change'])} |")
        lines.append("")
    lines += ["## Coverage and quality", "", f"- Dynamic outcomes by task: {metrics['dynamic_coverage']}",
              f"- Functional outcomes: {metrics['functional_outcomes']}",
              f"- Mean analysis seconds: {metrics['mean_seconds']}",
              f"- Candidates skipped (not generated): {len(skipped)}"]
    lines += [f"- Warning: {w}" for w in warnings]
    return "\n".join(lines) + "\n"


def read_labels(path: Path) -> tuple[dict, dict | None]:
    """Return ({candidate_id: label}, first-pass agreement if reviewer columns are present)."""
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not {"candidate_id", "label"} <= set(reader.fieldnames or ()):
            raise ValueError(f"{path} needs candidate_id and label columns")
        rows = list(reader)
    labels = {}
    for row in rows:
        label = row["label"].strip()
        if row["candidate_id"] in labels:
            raise ValueError(f"Duplicate label for {row['candidate_id']}")
        if label and label not in LABELS:
            raise ValueError(f"Unknown label {label!r} for {row['candidate_id']}")
        labels[row["candidate_id"]] = label
    agreement = None
    if rows and {"reviewer_a", "reviewer_b"} <= set(rows[0]):
        agreed = sum(r["reviewer_a"] == r["reviewer_b"] for r in rows)
        agreement = {"pairs": len(rows), "agreed": agreed, "agreement": _ratio(agreed, len(rows))}
    return labels, agreement


def _write_csv(path: Path, columns: list[str], rows: list[dict], mode: str = "w") -> None:
    with path.open(mode, newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_label_sheet(paths: list[Path], out: Path) -> int:
    """Blank review sheet with no detector output, ordered independently of model and run."""
    candidates, _ = load_candidates(paths)
    ordered = sorted(candidates, key=lambda c: digest(c["candidate_id"].encode()))
    _write_csv(out, SHEET_COLUMNS, [{**c, "target_cwe": c["cwe"], "label": "", "notes": ""} for c in ordered], "x")
    return len(ordered)


def merge_labels(first: Path, second: Path, out: Path) -> dict:
    """Combine two complete first-pass sheets; disagreements get a blank label to adjudicate."""
    a, _ = read_labels(first)
    b, _ = read_labels(second)
    if set(a) != set(b):
        raise ValueError("Reviewer sheets cover different candidates")
    incomplete = [c for c, label in {**a, **b}.items() if not label or not a[c] or not b[c]]
    if incomplete:
        raise ValueError(f"{len(incomplete)} candidates are not labeled by both reviewers")
    rows = [{"candidate_id": c, "reviewer_a": a[c], "reviewer_b": b[c],
             "label": a[c] if a[c] == b[c] else "", "adjudication_note": ""} for c in sorted(a)]
    _write_csv(out, MERGED_COLUMNS, rows, "x")
    agreed = sum(r["label"] != "" for r in rows)
    return {"pairs": len(rows), "agreed": agreed, "agreement": _ratio(agreed, len(rows)),
            "to_adjudicate": len(rows) - agreed}


def run_metrics(candidate_paths: list[Path], result_paths: list[Path], out: Path,
                labels_path: Path | None = None) -> dict:
    candidates, skipped = load_candidates(candidate_paths)
    results, warnings = load_results(result_paths)
    labels, agreement = read_labels(labels_path) if labels_path else ({}, None)
    unknown = set(labels) - {c["candidate_id"] for c in candidates}
    if unknown:
        raise ValueError(f"{len(unknown)} labels refer to unknown candidates, e.g. {sorted(unknown)[0]}")
    rows = build_table(candidates, results, labels)
    metrics = compute_metrics(rows)
    metrics.update(skipped=skipped, warnings=warnings, reviewer_agreement=agreement)
    out.mkdir(parents=True, exist_ok=False)
    _write_csv(out / "evaluation_table.csv", TABLE_COLUMNS, rows)
    _write_csv(out / "error_analysis.csv", ERROR_COLUMNS, error_rows(rows, results))
    write_json(out / "metrics.json", metrics)
    (out / "report.md").write_text(format_report(metrics, skipped, warnings, agreement), encoding="utf-8")
    return metrics
