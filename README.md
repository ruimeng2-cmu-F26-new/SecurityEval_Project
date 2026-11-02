# SecurityEval_Project

AI information security course project by Ruimeng Chen, Susie Zhong, and Jiayi Li.

This project evaluates LLM-generated Python code using **Bandit, custom AST rules,
and functional and security tests**. We will compare the findings from these methods
before exploring LLM-based repair. Automated repair is outside the first-week scope.

## Current Status

- Implemented: a Python 3.11 project scaffold, three traceable samples adapted from
  SecurityEval, shared JSON schemas, Member 1's OpenAI Responses API generation and
  artifact recording, offline harness tests, and integration points for all three members.
- Not yet run: live LLM generation. API credentials are pending.
- Implemented (Member 2): Bandit integration, two custom AST rules validated on hand-written
  fixtures, and `security-eval static`. See [Static Analysis](docs/STATIC_ANALYSIS.md).
- Implemented (Member 3): a bounded Docker runner and functional/security tests
  for the three adapted samples. See [Docker execution](docker/README.md).
- Selected for the first experiment: `gpt-6-luna` and `gpt-6.1-sol`, ten independent
  requests per task-model pair at medium reasoning effort (60 candidates total).
  The 60-record dry run is complete; live generation and evaluation remain pending.
- By default, `pytest` tests the harness only. **Passing harness tests does not establish
  the functionality or security of generated code.** The `generated` status indicates
  a complete response containing parseable Python and the expected entry point;
  it does not establish correctness or security.

## Quick Start

Run all commands from the repository root. Python **3.11.x** is required. The Python 3.9
installation bundled with some macOS versions is not supported. If a project `.venv`
with Python 3.11 already exists, activate it; otherwise, create one:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install --no-deps -e .
python -m pytest -q
security-eval samples
```

`requirements.txt` pins the dependency versions used for local validation.
`pyproject.toml` defines package metadata, the Python version requirement, and optional
dependencies. Keep virtual environments, API keys, downloaded source caches, and
unreviewed experiment artifacts out of version control.

If `code .` is unavailable on macOS, open the project using the installed VS Code launcher:

```bash
"/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code" .
```

To enable `code .`, run `Shell Command: Install 'code' command in PATH` from the
VS Code Command Palette, then open a new terminal.

## Selected Samples and Function Interfaces

| Sample ID | Upstream record ID | Adapted entry point | Main adaptation |
|---|---|---|---|
| `sql_delete_user` | `CWE-089_author_1.py` | `remove_user(conn, username) -> int` | Replace MySQL with SQLite and accept a caller-owned connection |
| `command_allowlist` | `CWE-078_author_1.py` | `execute_command(command) -> str` | Replace interactive input with an argument and define allowed commands and errors |
| `path_read_file` | `CWE-022_codeql_1.py` | `read_file(base_dir, filename) -> bytes` | Replace Flask with a function and define directory boundaries and exceptions |

`data/samples.jsonl` records each original prompt, adapted prompt, modification,
selection rationale, functional requirement, security requirement, upstream commit,
and SHA-256 hash. Original prompts were extracted from the upstream dataset; locally
written code is not represented as upstream data.

**These prompts add explicit security requirements and constitute an adapted experiment.
Results must not be reported as scores on the original SecurityEval benchmark.**
The CWE label identifies the upstream sample category; it does not establish that
any particular generated candidate contains that vulnerability.

Source: [s2e-lab/SecurityEval](https://github.com/s2e-lab/SecurityEval), pinned to commit
`6f4fb70f782c6d47b02ea24341e8ef8c1eb04a6a`.
Download the pinned dataset once, then verify the original prompts offline:

```bash
python scripts/verify_source.py --download
python scripts/verify_source.py
```

No standalone LICENSE file was found at this upstream revision. Upstream attribution
is retained; this project does not assign a new license to the upstream data.

Reference: Mohammed Latif Siddiq and Joanna C. S. Santos, *SecurityEval Dataset: Mining
Vulnerability Examples to Evaluate Machine Learning-Based Code Generation Techniques*,
MSR4P&S 2022. [DOI](https://doi.org/10.1145/3549035.3561184).

## Member 1: Code Generation and Artifact Recording

Prepare the complete 60-candidate experiment without making an API call or producing
`code.py`:

```bash
security-eval generate-experiment \
  --models gpt-6-luna gpt-6.1-sol \
  --runs 10 --reasoning-effort medium --max-output-tokens 25000 \
  --dry-run --out artifacts/member1-experiment-dry-run-001
```

The first experiment makes ten independent requests for each of three tasks and two
models: 60 candidates total. Use a dated model snapshot when available; otherwise retain
the requested and returned model IDs, response ID, timestamp, metadata, and hashes.
Preserve every initial output rather than selecting only favorable candidates.

Live generation requires `OPENAI_API_KEY` in the local environment. The following zsh
commands read the key without displaying it or placing its value in shell history:

```bash
read -s "OPENAI_API_KEY?OpenAI API key: "
export OPENAI_API_KEY
printf '\n'
security-eval generate-experiment \
  --models gpt-6-luna gpt-6.1-sol \
  --runs 1 --reasoning-effort medium --max-output-tokens 25000 \
  --out artifacts/member1-pilot-001
unset OPENAI_API_KEY
```

For bash, replace the `read` command with
`read -s -p 'OpenAI API key: ' OPENAI_API_KEY`.
`.env.example` documents the variables; the application does not automatically load `.env`.
`OPENAI_MODEL` can be used instead of `--model`.

The `--temperature` parameter is omitted by default. Set it only when the selected
model supports it. Requests have a 90-second timeout and no automatic retries.

The experiment writes `manifest.json` and one subdirectory per candidate. Each attempt saves
`sample.json`, `request.json`, and `generation.json`. After receiving
a response, it also saves `response.json` and `completion.txt`, plus `code.py` when source
can be extracted. Records include request and code hashes, requested and returned model
IDs, timestamps, response ID, usage, and error status. Existing output directories are
never overwritten. Incomplete responses, refusals, empty outputs, and syntax errors are
not marked successful.

Candidate code is parsed but **never imported or executed** during generation.
Experiment artifacts are ignored by Git by default; review them before archiving or sharing.

API reference: [Responses API](https://developers.openai.com/api/reference/python/resources/responses/methods/create).
The frozen experimental design is in [Experiment Plan](docs/EXPERIMENT_PLAN.md).
The complete Member 1 run and review checklist is in
[Member 1 Handoff](docs/MEMBER1_HANDOFF.md).

## Analyzer Integration

```bash
security-eval evaluate artifacts/sql-live-001 --out artifacts/sql-analysis-001
security-eval validate analysis artifacts/sql-analysis-001/bandit.json
```

Bandit, AST, and Docker adapters are connected. Dynamic execution requires a locally
built `security-eval-tests:dev` image and a running Docker engine; infrastructure
failures are recorded as `error`. To run only static analysis:

```bash
security-eval static artifacts/sql-live-001 --out artifacts/sql-static-001
```

This prints a summary and writes `static_summary.json` plus per-tool contracts and evidence;
see [Static Analysis](docs/STATIC_ANALYSIS.md).
The pipeline verifies the candidate's code hash to ensure that each analyzer receives
the same source. Dynamic testing executes candidate code only inside the restricted Docker container.

Analyzer implementations must return records that pass the schemas described in
[Shared Contracts](docs/INTERFACES.md). An empty findings list does not establish safety.
Distinguish an analyzer that did not run, an execution error, and a completed run with
no findings.

## Team Responsibilities and Collaboration

| Member | Primary files and directories | Expected deliverables |
|---|---|---|
| Member 1 / Susie Zhong | `data/`, `generation.py`, `scripts/verify_source.py` | 60 live-generated candidates with request, response, hash, usage, and cost records |
| Member 2 / Jiayi Li| `analyzers/static.py`, new rule modules, and rule unit tests | Bandit integration, one or two AST rules, and actual JSON findings |
| Member 3 | `analyzers/dynamic.py`, `tests/candidates/`, `docker/` | Isolated execution, functional and security tests, and supporting evidence |

See [Shared Contracts](docs/INTERFACES.md) for the complete handoff. Start with
`sql_delete_user`, then extend the pipeline to the other two samples. Coordinate changes
to shared schemas and function signatures before implementation.

After the scaffold is available on `main`, each member should pull the same baseline
and create a separate branch:

```bash
git switch main
git pull --ff-only origin main
git switch -c member2-static  # Member 3 should use member3-dynamic.
```

Run the harness tests and the relevant module tests before submitting a pull request
to `main`. Keep API keys and local virtual environments out of the repository.
Report only completed work supported by recorded evidence; placeholder results must
not be presented as successful evaluations.

Local validation details are recorded in [Validation](docs/VALIDATION.md).
