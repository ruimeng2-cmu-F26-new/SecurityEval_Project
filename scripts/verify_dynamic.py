"""Real Docker checks using hand-written controls, never benchmark/model results."""
import argparse
import json
from collections import Counter
from pathlib import Path

from security_eval.analyzers.dynamic import DockerPytestAnalyzer
from security_eval.contracts import load_samples, write_json
from security_eval.dynamic_runner import decide

ROOT = Path(__file__).resolve().parents[1]
# (fixture, sample, expected D decision, expected functional outcome, timeout); None = run error.
CASES = [
    ("sql_safe", "sql_delete_user", "no", "passed", 30),
    ("sql_unsafe", "sql_delete_user", "yes", "failed", 30),
    ("sql_double_quote_unsafe", "sql_delete_user", "yes", "failed", 30),
    ("sql_noop", "sql_delete_user", "no", "failed", 30),
    ("sql_rejects_quotes", "sql_delete_user", "no", "failed", 30),
    ("command_safe", "command_allowlist", "no", "passed", 30),
    ("command_unsafe", "command_allowlist", "yes", "failed", 30),
    ("command_shell_filtered", "command_allowlist", "yes", "passed", 30),
    ("command_literal", "command_allowlist", "no", "failed", 30),
    ("path_safe", "path_read_file", "no", "passed", 30),
    ("path_unsafe", "path_read_file", "yes", "failed", 30),
    ("path_prefix_unsafe", "path_read_file", "yes", "failed", 30),
    ("path_lenient", "path_read_file", "no", "failed", 30),
    ("import_error", "sql_delete_user", None, None, 30),
    ("hangs", "sql_delete_user", None, None, 3),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--image", default="security-eval-tests:dev")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    samples = {s["sample_id"]: s for s in load_samples(ROOT / "data/samples.jsonl")}
    failed = False
    for fixture, sample_id, expected, functional, timeout in CASES:
        analyzer = DockerPytestAnalyzer(args.out / fixture, image=args.image, timeout=timeout)
        result = analyzer.analyze(ROOT / f"tests/fixtures/dynamic/{fixture}.py", samples[sample_id], "handwritten-control:" + fixture)
        write_json(args.out / (fixture + ".json"), result)
        outcomes = dict(Counter(t["outcome"] for t in result["tests"]))
        environment = json.loads((args.out / fixture / "environment.json").read_text())
        decision = decide(result)
        ok = environment["cleanup_confirmed"] and not decision["unexplained_security_failures"] and (
            (result["status"] == "completed" and decision["d_decision"] == expected
             and decision["functional"] == functional) if expected is not None
            else result["status"] == "error" and decision["d_decision"] == "inconclusive" and (
                "Timeout" in str(result["error"]) if fixture == "hangs"
                else "setup or teardown" in str(result["error"])
            )
        )
        print(f"{fixture}: {'OK' if ok else 'FAIL'} {result['status']} D={decision['d_decision']} "
              f"functional={decision['functional']} {outcomes} "
              f"security_failed={[t.split('::')[-1] for t in decision['failed_security_tests']]} {result['error']}", flush=True)
        failed |= not ok
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
