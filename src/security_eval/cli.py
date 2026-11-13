import argparse
import json
import os
import sys
from pathlib import Path

from jsonschema.exceptions import ValidationError

from .contracts import load_samples, validate
from .evaluation import merge_labels, run_metrics, write_label_sheet
from .generation import generate, prepare, run_batch
from .generation import generate, prepare, run_batch, run_experiment
from .pipeline import evaluate
from .static_runner import all_completed, format_summary, run_static


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="SecurityEval project (Python 3.11)")
    commands = parser.add_subparsers(dest="command", required=True)
    listing = commands.add_parser("samples", help="Validate and list selected samples")
    listing.add_argument("--samples", type=Path, default=Path("data/samples.jsonl"))
    validation = commands.add_parser("validate", help="Validate one JSON contract")
    validation.add_argument("kind", choices=["sample", "generation", "analysis"])
    validation.add_argument("file", type=Path)
    evaluation = commands.add_parser("evaluate", help="Run available adapters; unfinished adapters report not_run")
    evaluation.add_argument("run_dir", type=Path)
    evaluation.add_argument("--out", type=Path, required=True)
    static = commands.add_parser("static", help="Run Bandit and custom AST rules on files or run directories")
    static.add_argument("paths", nargs="+", type=Path, help=".py files, generation run directories, or folders of them")
    static.add_argument("--out", type=Path, required=True, help="New directory; existing results are never overwritten")
    static.add_argument("--sample-id", help="Sample ID for a single plain .py file (default: derived from file name)")
    generation = commands.add_parser("generate", help="Generate one candidate or prepare a dry run")
    generation.add_argument("sample_id")
    generation.add_argument("--samples", type=Path, default=Path("data/samples.jsonl"))
    generation.add_argument("--model", default=os.environ.get("ANTHROPIC_MODEL"))
    generation.add_argument("--out", required=True, type=Path, help="New directory; existing results are never overwritten")
    generation.add_argument("--dry-run", action="store_true")
    generation.add_argument("--max-tokens", type=int, default=16000)
    generation.add_argument("--effort", choices=["low", "medium", "high", "xhigh", "max"], default="medium")
    batch = commands.add_parser("generate-batch", help="Generate one recorded attempt for every selected sample")
    batch.add_argument("--samples", type=Path, default=Path("data/samples.jsonl"))
    batch.add_argument("--model", default=os.environ.get("ANTHROPIC_MODEL"))
    batch.add_argument("--out", required=True, type=Path, help="New batch directory; existing results are never overwritten")
    batch.add_argument("--dry-run", action="store_true")
    batch.add_argument("--temperature", type=float)
    batch.add_argument("--max-output-tokens", type=int, default=4096)
    batch.add_argument("--reasoning-effort", choices=["none", "minimal", "low", "medium", "high", "xhigh"])
    sheet = commands.add_parser("label-sheet", help="Write a blank review sheet with no detector output")
    sheet.add_argument("paths", nargs="+", type=Path, help="Experiment or generation run directories")
    sheet.add_argument("--out", type=Path, required=True, help="New CSV file")
    merging = commands.add_parser("merge-labels", help="Combine two reviewer sheets and list disagreements")
    merging.add_argument("first", type=Path)
    merging.add_argument("second", type=Path)
    merging.add_argument("--out", type=Path, required=True, help="New CSV file; adjudicate blank labels in it")
    metrics = commands.add_parser("metrics", help="Compute detection metrics from results and manual labels")
    metrics.add_argument("--candidates", nargs="+", type=Path, required=True,
                         help="Experiment or generation run directories")
    metrics.add_argument("--results", nargs="+", type=Path, required=True,
                         help="Directories searched for bandit.json, ast.json and pytest-docker.json")
    metrics.add_argument("--labels", type=Path, help="Adjudicated labels CSV")
    metrics.add_argument("--out", type=Path, required=True, help="New directory; existing results are never overwritten")
    batch.add_argument("--max-tokens", type=int, default=16000)
    batch.add_argument("--effort", choices=["low", "medium", "high", "xhigh", "max"], default="medium")
    experiment = commands.add_parser(
        "generate-experiment",
        help="Generate or dry-run repeated independent candidates across multiple models",
    )
    experiment.add_argument("--samples", type=Path, default=Path("data/samples.jsonl"))
    experiment.add_argument("--models", nargs="+", required=True)
    experiment.add_argument("--runs", type=int, default=10)
    experiment.add_argument("--out", required=True, type=Path,
                            help="New experiment directory; existing results are never overwritten")
    experiment.add_argument("--dry-run", action="store_true")
    experiment.add_argument("--max-tokens", type=int, default=16000)
    experiment.add_argument("--effort", choices=["low", "medium", "high", "xhigh", "max"],
                            default="medium")
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            validate(args.kind, json.loads(args.file.read_text(encoding="utf-8")))
            print("Valid " + args.kind + " contract")
        elif args.command == "samples":
            for sample in load_samples(args.samples):
                print(f'{sample["sample_id"]}\t{sample["cwe"]}\t{sample["signature"]}')
        elif args.command == "evaluate":
            results = evaluate(args.run_dir, args.out)
            print(json.dumps({r["tool"]: r["status"] for r in results}))
            return 0 if all(r["status"] == "completed" for r in results) else 1
        elif args.command == "label-sheet":
            print(f"Wrote {write_label_sheet(args.paths, args.out)} candidates to {args.out}")
        elif args.command == "merge-labels":
            print(json.dumps(merge_labels(args.first, args.second, args.out)))
        elif args.command == "metrics":
            result = run_metrics(args.candidates, args.results, args.out, args.labels)
            print(json.dumps({"pairs": result["pairs"], "labels": result["labels"],
                              "skipped": len(result["skipped"]), "report": str(args.out / "report.md")}))
        elif args.command == "static":
            summary = run_static(args.paths, args.out, args.sample_id)
            print(format_summary(summary))
            print(f"Results: {args.out / 'static_summary.json'}")
            return 0 if all_completed(summary) else 1
        elif args.command == "generate-experiment":
            manifest = run_experiment(
                load_samples(args.samples), args.out, args.models,
                runs=args.runs, dry_run=args.dry_run,
                max_tokens=args.max_tokens,
                effort=args.effort,
            )
            print(json.dumps({
                "status": manifest["status"],
                "expected_candidates": manifest["expected_candidates"],
                "status_counts": manifest["status_counts"],
                "manifest": str(args.out / "manifest.json"),
            }))
            return 0 if manifest["status"] == "complete" else 1
        elif args.command == "generate-batch":
            if not args.model:
                raise ValueError("Set --model or ANTHROPIC_MODEL explicitly")
            manifest = run_batch(
                load_samples(args.samples), args.out, args.model,
                dry_run=args.dry_run, max_tokens=args.max_tokens, effort=args.effort,
            )
            print(json.dumps({"status": manifest["status"], "manifest": str(args.out / "manifest.json")}))
            return 0 if manifest["status"] == "complete" else 1
        else:
            if not args.model:
                raise ValueError("Set --model or ANTHROPIC_MODEL explicitly")
            samples = {s["sample_id"]: s for s in load_samples(args.samples)}
            if args.sample_id not in samples:
                raise ValueError("Unknown sample_id")
            operation = prepare if args.dry_run else generate
            record = operation(samples[args.sample_id], args.out, args.model,
                               max_tokens=args.max_tokens, effort=args.effort)
            print(json.dumps({"status": record["status"], "record": str(args.out / "generation.json")}))
            return 1 if record["status"] == "error" else 0
        return 0
    except (ValueError, OSError, ValidationError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
