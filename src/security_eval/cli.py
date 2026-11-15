import argparse
import json
import os
import sys
from pathlib import Path

from jsonschema.exceptions import ValidationError

from .contracts import load_samples, validate
from .generation import generate, prepare, run_batch
from .pipeline import evaluate
from . import dynamic_runner
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
    dynamic = commands.add_parser("dynamic", help="Run Docker functional/security tests on generation run directories")
    dynamic.add_argument("paths", nargs="+", type=Path, help="Experiment directories or generation run directories")
    dynamic.add_argument("--out", type=Path, required=True, help="New directory; existing results are never overwritten")
    dynamic.add_argument("--image", default="security-eval-tests:dev")
    dynamic.add_argument("--timeout", type=int, default=60, help="Seconds allowed for one candidate's container")
    static = commands.add_parser("static", help="Run Bandit and custom AST rules on files or run directories")
    static.add_argument("paths", nargs="+", type=Path, help=".py files, generation run directories, or folders of them")
    static.add_argument("--out", type=Path, required=True, help="New directory; existing results are never overwritten")
    static.add_argument("--sample-id", help="Sample ID for a single plain .py file (default: derived from file name)")
    generation = commands.add_parser("generate", help="Generate one candidate or prepare a dry run")
    generation.add_argument("sample_id")
    generation.add_argument("--samples", type=Path, default=Path("data/samples.jsonl"))
    generation.add_argument("--model", default=os.environ.get("OPENAI_MODEL"))
    generation.add_argument("--out", required=True, type=Path, help="New directory; existing results are never overwritten")
    generation.add_argument("--dry-run", action="store_true")
    generation.add_argument("--temperature", type=float)
    generation.add_argument("--max-output-tokens", type=int, default=4096)
    generation.add_argument("--reasoning-effort", choices=["none", "minimal", "low", "medium", "high", "xhigh"])
    batch = commands.add_parser("generate-batch", help="Generate one recorded attempt for every selected sample")
    batch.add_argument("--samples", type=Path, default=Path("data/samples.jsonl"))
    batch.add_argument("--model", default=os.environ.get("OPENAI_MODEL"))
    batch.add_argument("--out", required=True, type=Path, help="New batch directory; existing results are never overwritten")
    batch.add_argument("--dry-run", action="store_true")
    batch.add_argument("--temperature", type=float)
    batch.add_argument("--max-output-tokens", type=int, default=4096)
    batch.add_argument("--reasoning-effort", choices=["none", "minimal", "low", "medium", "high", "xhigh"])
    args = parser.parse_args(argv)
    try:
        if args.command == "dynamic":
            summary = dynamic_runner.run_dynamic(args.paths, args.out, args.image, args.timeout,
                                                 progress=lambda line: print(line, flush=True))
            print(json.dumps({"overall": summary["overall"], "skipped": len(summary["skipped"]),
                              "summary": str(args.out / "dynamic_summary.md")}))
            return 0 if dynamic_runner.all_completed(summary) else 1
        elif args.command == "validate":
            validate(args.kind, json.loads(args.file.read_text(encoding="utf-8")))
            print("Valid " + args.kind + " contract")
        elif args.command == "samples":
            for sample in load_samples(args.samples):
                print(f'{sample["sample_id"]}\t{sample["cwe"]}\t{sample["signature"]}')
        elif args.command == "evaluate":
            results = evaluate(args.run_dir, args.out)
            print(json.dumps({r["tool"]: r["status"] for r in results}))
            return 0 if all(r["status"] == "completed" for r in results) else 1
        elif args.command == "static":
            summary = run_static(args.paths, args.out, args.sample_id)
            print(format_summary(summary))
            print(f"Results: {args.out / 'static_summary.json'}")
            return 0 if all_completed(summary) else 1
        elif args.command == "generate-batch":
            if not args.model:
                raise ValueError("Set --model or OPENAI_MODEL explicitly")
            manifest = run_batch(
                load_samples(args.samples), args.out, args.model,
                dry_run=args.dry_run, temperature=args.temperature,
                max_output_tokens=args.max_output_tokens,
                reasoning_effort=args.reasoning_effort,
            )
            print(json.dumps({"status": manifest["status"], "manifest": str(args.out / "manifest.json")}))
            return 0 if manifest["status"] == "complete" else 1
        else:
            if not args.model:
                raise ValueError("Set --model or OPENAI_MODEL explicitly")
            samples = {s["sample_id"]: s for s in load_samples(args.samples)}
            if args.sample_id not in samples:
                raise ValueError("Unknown sample_id")
            operation = prepare if args.dry_run else generate
            record = operation(samples[args.sample_id], args.out, args.model,
                               temperature=args.temperature, max_output_tokens=args.max_output_tokens,
                               reasoning_effort=args.reasoning_effort)
            print(json.dumps({"status": record["status"], "record": str(args.out / "generation.json")}))
            return 1 if record["status"] == "error" else 0
        return 0
    except (ValueError, OSError, ValidationError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
