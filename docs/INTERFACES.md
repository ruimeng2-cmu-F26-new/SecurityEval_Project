# Shared contracts v1.0

All JSON files use UTF-8. Schemas live in `src/security_eval/schemas/` and reject unknown
fields. Use `security_eval.contracts.validate(kind, record)` before writing any result.
IDs are stable; do not rename sample IDs or entry points independently.

## Sample and generation

- `sample.json`: copy of one row from `data/samples.jsonl`. `original_prompt` is upstream;
  `adapted_prompt` is what the LLM receives. `source` identifies commit, dataset hash,
  original ID and original prompt hash. Functional/security requirements belong to
  this **adapted** experiment, not the original benchmark.
- `generation.json`: `prepared` means no API call; `generated` means a complete response
  with parseable source and the named top-level function; `error` records failure.
  Syntax validation does not prove signature compliance, functionality or security.
- Repeated experiments add a stable `candidate_id` and positive `run_index`. Records
  retain SHA-256 hashes for the adapted prompt, request JSON, response JSON, and exact
  candidate bytes. Token usage and the standard-processing cost estimate are recorded
  when the requested model has a documented price in the harness.
- `request.json` is the actual payload; `response.json` is the unmodified SDK response
  serialized as JSON, and `completion.txt` is the complete output text. Only a single
  enclosing Markdown fence is removed from candidate source. No repair is attempted.
- All generation paths are relative to the generation directory. Code hash uses the
  exact UTF-8 bytes of `code.py`. Preserve the initial candidate for every detector.
- `generate-experiment` creates one independent request per task-model-run combination.
  It does not pass a conversation ID or previous response ID between candidates.

## Analyzer API (Member 2 and Member 3)

```python
class Analyzer:
    def analyze(self, code_path: Path, sample: dict, run_id: str) -> dict:
        ...  # Return an analysis.json-compatible dictionary.
```

`pipeline.evaluate()` passes the same resolved file to each adapter. Implement
`BanditAnalyzer` and `ASTAnalyzer` in `analyzers/static.py`, and
`DockerPytestAnalyzer` in `analyzers/dynamic.py`. Never modify the candidate.
The pipeline supplies `evidence_dir=out / "pytest-docker"` to the dynamic adapter;
without this explicit configuration it returns `not_run`. Evidence paths are relative
to the parent of that directory.
`run_id` currently combines request and code hashes; use separate output directories
for repeated attempts. `tool` is one of `bandit`, `ast`, `pytest-docker`.

| Field | Meaning |
|---|---|
| `schema_version` | `1.0` |
| `sample_id`, `run_id`, `code_sha256` | Link all observations to the same input |
| `status` | `not_run`, `completed`, or `error` |
| `tool_version` | Actual tool/rule-set version; required for completed runs |
| `started_at`, `completed_at` | UTC ISO-8601 timestamps; null if unavailable |
| `findings` | Static/dynamic observations with rule_id, cwe, severity, confidence, message, line, evidence |
| `tests` | test_id, category (`functional`/`security`), outcome (`passed`/`failed`/`error`/`skipped`), message |
| `evidence_files` | Paths relative to the analysis output directory; actual logs or structured reports |
| `error` | null or `{type, message}`; sanitize secrets |
| `notes` | Limits, context, and unimplemented steps |

`completed` means the tool ran, not that code is secure or tests passed. A vulnerability
claim needs evidence and review. Normal exceptions, syntax/import errors, collection
failures, timeouts and missing tools are not automatically vulnerabilities.
`not_run` may not contain findings or tests. `completed` requires tool version, start/end
times, at least one evidence path and no tool-level error. Findings use lowercase
`low/medium/high/unknown`; line is one-based or null.

### Member 2 checklist

1. Run Bandit using an argument list and a timeout; retain its JSON output and stderr.
   Distinguish exit 1 with findings from a tool failure; inspect parse errors too.
2. Implement 1–2 AST rules aligned with these samples. Parse candidate code as data;
   never import it. State limitations (e.g., aliases and interprocedural flows).
3. Test known safe/unsafe hand-written fixtures **labeled as rule tests**, separately
   from model generations. Record actual tool versions and evidence files.
4. Return our analysis contract; do not replace it with raw Bandit JSON.

Bandit is an optional dependency: `python -m pip install '.[static]'`; `requirements.txt`
pins `bandit==1.9.4`. `BanditAnalyzer(out_dir)` and `ASTAnalyzer(out_dir)` write evidence
into the analysis output directory. Usage, rules and limitations: `docs/STATIC_ANALYSIS.md`. Do not accidentally scan `.venv` or the entire upstream corpus.

### Member 3 checklist

1. Start with `sql_delete_user`; `tests/candidates/README.md` and sample requirements
   specify normal and malicious input behavior. Agree on these expectations with Member 1.
2. Implement restricted Docker execution before importing candidates. See `docker/README.md`.
3. Capture each test outcome, environment/image identity, command, exit code and logs.
   Security assertions should fail when a violation is observed, not simply when any
   exception happens. Separate functional regression from security test failure.
4. Default root `pytest` runs only harness unit tests. Candidate tests must run inside
   the container and be reported separately; do not count skipped tests as passing.

## Evidence and reporting

Unit tests use explicitly synthetic API fixtures and temporary directories. They are
harness checks, never SecurityEval scores or evidence of a live API call. Prepared
requests have no generated code. Static rule tests use hand-written fixtures in
`tests/fixtures/static/`; they are not candidate results. No Docker results are claimed.
Use hashes plus reviewed evidence to build a later comparison table; do not infer
that dynamic analysis improves recall until actual runs support that claim.
