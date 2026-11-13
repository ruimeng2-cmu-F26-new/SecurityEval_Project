# Static analysis (Member 2)

Bandit is the baseline scanner; three custom AST rules add input-to-sink checks for the
selected samples. Both produce the shared `analysis.json` contract, plus a combined
`static_summary.json`. **Every finding is an unverified potential issue**, not a confirmed
vulnerability; "no findings" does not mean the code is secure.

## Usage

Set up the environment as described in the README Quick Start (`requirements.txt` pins
`bandit==1.9.4`), then run:

```bash
security-eval static artifacts/sql-live-001 --out artifacts/sql-static-001   # one generation run
security-eval static artifacts/ --out artifacts/static-all-001               # every run dir in artifacts/
security-eval static path/to/code.py --sample-id sql_delete_user --out artifacts/static-file-001
python -m pytest -q tests/unit/test_static.py                                # rule validation
```

Inputs may be `.py` files, generation run directories (with `generation.json`; status and
code hash are verified as in `evaluate`), or a folder with such files and directories (not
recursive). Exit code: 0 if every scan completed, 1 if any scan or input failed, 2 for
usage errors (e.g. the output directory already exists; results are never overwritten).
`security-eval evaluate` runs the same two analyzers with Member 3's adapter.

## Output

```
<out>/static_summary.json          per-target status + flat list of all static findings
<out>/<target>/bandit.json         analysis contract (tool=bandit)
<out>/<target>/ast.json            analysis contract (tool=ast)
<out>/<target>/bandit.raw.json     unmodified Bandit JSON output (evidence)
<out>/<target>/bandit.stderr.txt   Bandit stderr (evidence)
<out>/<target>/ast_rules.json      rule set, descriptions, limitations and findings (evidence)
```

Each `static_summary.json` finding has `target, sample_id, source_file, tool, rule_id, cwe,
severity, confidence, line, message, evidence, validation_status`. `validation_status` is
always `unverified` here; set it later from review or dynamic tests. Per-target results
report `outcome` as `findings`, `no_findings` or `error`; bad inputs appear as `input_error`.
Bandit rule IDs (e.g. `B608`) keep their original severity, confidence and CWE; the
`tool` field separates them from `AST-*` findings.

## Bandit integration

Runs `python -m bandit -f json -q --ignore-nosec <file>` with a 120 s timeout and default
plugins. `--ignore-nosec` stops generated code from suppressing the baseline with
`# nosec`. Bandit exits 0 even when it cannot parse a file and only lists it under
`errors`, so a non-empty `errors` list is reported as `status: error`. Exit 1 must match
non-empty results; anything else is a tool failure.

## Custom AST rules (`analyzers/ast_rules.py`, rule set 0.2.0)

A value is *input-derived* if it is a parameter of the enclosing function, a call to
`input()`, or a local variable assigned (transitively) from one. Code is parsed with
`ast.parse` and never imported or executed.

| Rule | Sample | Reports | Cannot determine |
|---|---|---|---|
| `AST-SQL-001` (CWE-089, high) | `sql_delete_user` | `.execute/.executemany/.executescript` whose SQL text (first argument) is input-derived | Sanitization or trusted input; flows through other functions, attributes, containers, globals; any method named `execute` counts as SQL |
| `AST-CMD-001` (CWE-078) | `command_allowlist` | `subprocess.*`/`os.system`/`os.popen` with an input-derived command: through a shell (high), selecting the program without an allowlist-style comparison (medium), or after one (low) | Whether the comparison is correct or guards every path to the call; argument injection when the program name is constant; `os.exec*`/`spawn*`; `shell=<variable>` is treated as `shell=True` |
| `AST-PATH-001` (CWE-022) | `path_read_file` | File access through an input-derived path: no recognized containment check (high), or a check that leaves symlinks unresolved or uses a plain string prefix (medium) | Whether a recognized check really guards this access or is enforced; a trusted directory parameter counts as input; concurrent symlink races |

Taint tracking is intraprocedural and flow-insensitive: it ignores statement order and
branches, and any expression that mentions an input-derived name counts as input-derived
(e.g. `len(username)`), which can produce false positives. Imports and aliases such as
`import subprocess as sp` and `from subprocess import run` are resolved; `getattr` and
dynamic imports are not. `AST-PATH-001` also looks for guards in same-module functions
connected by calls, so a validation helper is recognized.

Bandit has no general path-traversal check, so `AST-PATH-001` keeps B1 from having zero
recall on `path_read_file` by construction. The allowlist handling in `AST-CMD-001` was
added after Member 3's safe handwritten control was reported at medium severity. Both
changes were made before any model candidate was analyzed.

To add a rule, write `check(tree, ctx) -> list[finding]` and append a `Rule` to `RULES`.

## Validation

`tests/fixtures/static/` holds **hand-written rule-test fixtures**, not SecurityEval
samples or LLM output. Lines marked `# expect: <RULE>` must be reported, and nothing else
may be. `tests/unit/test_static.py` checks:

- the exact (rule, line) pairs for the unsafe and safe fixtures of each rule;
- the severity split of the command and path rules;
- the expected AST results on Member 3's handwritten controls;
- contract validity and evidence files;
- syntax errors in both tools, Bandit's no-findings case and batch input errors;
- that results are never overwritten.

As a sanity check, the suite was run against deliberately broken copies of the rules and
the metric code. Two survivors exposed missing allowlist cases, which were added; every
one of these broken copies now makes at least one test fail. Passing fixtures show the rules behave as designed on these
patterns; they do not measure false-positive or false-negative rates on real code.

## Experiment workflow

The full comparison is defined in [Evaluation Protocol](EVALUATION_PROTOCOL.md).

```bash
# 1. Label from code only, before looking at any detector output.
security-eval label-sheet artifacts/experiment-001 --out reviewer_a.csv   # repeat for reviewer_b.csv
security-eval merge-labels reviewer_a.csv reviewer_b.csv --out labels.csv # fill blank labels by adjudication

# 2. Run the detectors (Bandit, AST and Docker tests) on every generated candidate.
for run in artifacts/experiment-001/*/; do
  security-eval evaluate "$run" --out "artifacts/experiment-001-results/$(basename "$run")"
done

# 3. Join everything and compute metrics.
security-eval metrics --candidates artifacts/experiment-001 \
  --results artifacts/experiment-001-results --labels labels.csv --out artifacts/experiment-001-metrics
```

`evaluate` exits nonzero when a candidate cannot be evaluated, and the loop continues; failed
generations are listed as skipped. `metrics` writes `evaluation_table.csv`, `metrics.json`,
`report.md` and `error_analysis.csv` (B1 false positives and negatives with an empty
`category` column for manual error analysis). Omit `--labels` only to check that results
join correctly; do not read detector results before first-pass labeling is complete.

## Assumptions to confirm

- Member 1: candidates live in `<experiment>/<candidate_id>/` with `generation.json`,
  `sample.json` and `code.py`, as `generate-experiment` writes them.
- Member 3: `pytest-docker.json` stays an `analysis.json` record, with one category per test.
- Shared harness: `BanditAnalyzer(out_dir)` / `ASTAnalyzer(out_dir)` take the output
  directory for evidence files; `pipeline.evaluate` passes it.
