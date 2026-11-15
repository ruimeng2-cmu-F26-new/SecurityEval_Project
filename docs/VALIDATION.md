# Scaffold validation — 2026-10-19

These are actual local harness checks on macOS arm64, Python **3.11.17**.
They are not candidate functionality/security results and are not GitHub CI results.

| Check | Observed result |
|---|---|
| Install pinned requirements and editable package | Successful |
| `python -m pytest -q` | **27 passed** in the installed project |
| `python -m pip check` | No broken requirements found |
| `python scripts/verify_source.py --download` | 3 original prompts verified against pinned upstream data |
| `security-eval samples` | 3 validated sample records listed |
| Batch dry-run preparation for all 3 samples | `complete`; each sample is `prepared`, with no API call or generated code |
| `git diff --check` | No whitespace errors |

The tests exercise contract rejection, duplicate sample handling, batch preparation,
credential checks before batch output creation, pending analyzer
states, code extraction, missing credentials, API failure, empty/invalid/incomplete
outputs, preservation of raw output, prevention of candidate execution, the real
OpenAI SDK with an explicitly mocked HTTP transport, and pipeline hash checks.
Synthetic fixture responses exist only in temporary test directories.

## Not run / not implemented

- No live model request: API credentials and final model choice are pending.
- No Bandit or custom AST scan of an LLM-generated candidate (none exists yet); see below
  for the rule-fixture validation.
- At the scaffold stage, candidate Docker execution was pending; see Member 3 validation below.
- No security score, vulnerability discovery, detector comparison, or repair claim.

Prepared local artifacts are ignored by Git. Repeatable commands and interfaces are
in the README and INTERFACES.md. Run the next real experiment in a fresh output
directory to preserve the original records.

## Static analysis (Member 2) — 2026-10-19

Python 3.11.17, Bandit 1.9.4, AST rule set 0.1.0. These are rule tests on hand-written
fixtures, not results on generated candidates.

| Check | Observed result |
|---|---|
| `python -m pytest -q` (harness + static tests) | **35 passed** |
| Rule fixtures: exact expected (rule, line) pairs | `AST-SQL-001`: 5 reported in unsafe, 0 in safe; `AST-CMD-001`: 6 in unsafe, 0 in safe |
| Mutants of the rule code (5 deliberate breakages) | Each made at least one static test fail |
| `security-eval static tests/fixtures/static does_not_exist.py` | Completed scans; syntax-error file and missing path reported as errors without stopping the batch (exit 1) |
| Contracts written by that run | All pass `security-eval validate analysis` |
| `python -m pip check` | No broken requirements found |

## Member 3 dynamic execution — 2026-10-21

- Offline harness: **31 passed**; `git diff --check` clean.
- Seven real Docker handwritten-control checks completed with expected outcomes:
  SQL safe 7 passed; SQL unsafe 3 failed/4 passed; SQL noop 5 failed/2 passed;
  command safe 18 passed; path safe 9 passed; import failure recorded as error;
  infinite loop recorded as timeout error with a three-second execution deadline.
- Container removal was confirmed by querying Docker for every control, including
  timeout and import failure. Results are local validation, not model/benchmark scores.
- Evidence: local ignored `artifacts/member3-validation-20261021/`; each case has
  normalized analysis JSON, environment/commands, logs, and report when available.
- Full Dockerfile rebuild waited on remote Python base-image metadata and was canceled.
  Real checks used `security-eval-tests:validation`, derived from the existing local
  `security-eval-tests:dev` image with the new runner and current tests copied in.
  Exact built image identity is retained in each environment record. A clean online
  Dockerfile build remains to be verified; no clean-build success is claimed.
- Automatic repair remains unimplemented. No live LLM evaluation
  was performed during this Member 3 validation.

## Clean image build follow-up — 2026-10-21

The project owner subsequently ran `docker build --pull --no-cache -f
docker/Dockerfile -t security-eval-tests:clean .` successfully and verified all seven
controls with that image. All printed `OK`, including confirmed cleanup for import
failure and timeout. Local evidence is in `artifacts/member3-clean-check-001/`.
This supersedes the earlier clean-build limitation and remains handwritten-control
validation, not a live LLM experiment.

## Combined branch merge validation — 2026-10-21

After integrating Member 1/2 main changes with Member 3: `python -m pytest -q`
reported **48 passed in 1.80s** and `python -m pip check` found no broken requirements.
The pipeline tests exercise real Bandit/AST execution with synthetic Docker responses
and verify shared run/code identities and evidence paths. They do not claim a live
LLM run or a new real-Docker experiment.

## Member 3 impact-based security tests and batch runner — 2026-11-12

- Candidate tests were rewritten so that `security` tests fail only on an observed impact;
  contract checks moved to `functional`. No experiment candidate had been evaluated before
  this change, so no result is affected.
- `python -m pytest -q`: **51 passed**. Image rebuilt from `docker/Dockerfile`.
- `scripts/verify_dynamic.py`: all 15 handwritten controls `OK` in real Docker (5 vulnerable
  controls D positive, 8 safe or contract-only controls D negative, import failure and
  infinite loop inconclusive, cleanup confirmed). Evidence: local ignored
  `artifacts/member3-controls-20261112/`.
- Integration check in a temporary merge with `member1-experiment-60` and `Jiayi` (not
  committed): 94 unit tests passed; `security-eval dynamic` ran 24 synthetic candidates
  (the handwritten controls served through a fake client, no API call) in real Docker, and
  `security-eval metrics` read the output with the same decision for all 24 rows.
- Not done: the 60 formal candidates have not been generated or shared, so there are no
  experiment results for D yet.
