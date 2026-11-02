# Member 1 Handoff

## Scope and status

Member 1 owns sample selection, prompt adaptation, code generation, and generation
records. The framework, three sample contracts, source verification, and batch-generation
command are complete. Live generation remains pending until a local Anthropic API key is
available. No live output or security result is claimed before that run finishes.

## Fixed detection-experiment configuration

| Setting | Value |
|---|---|
| Provider | Anthropic Messages API |
| Models | `claude-haiku-5-5`, `claude-sonnet-5-5` |
| Effort | `medium` |
| Thinking | `adaptive` |
| Maximum output tokens | `16000` |
| Temperature / top-p / top-k | Omitted |
| Retry policy | No automatic retries |
| Attempts | Ten independent requests per task-model combination |
| Total candidates | 60 |

Use a dated snapshot when one is available. Otherwise retain the requested model,
returned model, response ID, UTC timestamp, and complete response metadata. All task-model
combinations use the same settings. Preserve failed, refused, incomplete, or syntactically
invalid outputs as recorded errors; do not silently regenerate or select a more favorable
candidate. The complete design is in `docs/EXPERIMENT_PLAN.md`.

## Selected sample contracts

| Sample ID | Required entry point | Primary test focus |
|---|---|---|
| `sql_delete_user` | `remove_user(conn, username) -> int` | Exact deletion, quoted usernames, SQL injection input, caller-owned transaction |
| `command_allowlist` | `execute_command(command) -> str` | `pwd` and `echo`, unsupported commands, shell metacharacters, command substitution |
| `path_read_file` | `read_file(base_dir, filename) -> bytes` | In-base files, missing files, traversal, absolute paths, escaping symlinks |

The complete requirements and the original/adapted prompt distinction are in
`data/samples.jsonl`. Changes to signatures or expected behavior must be agreed on before
Member 2 or Member 3 writes analysis logic or candidate tests.

## Live generation

Before any paid call, prepare and review all 60 requests:

```bash
security-eval generate-experiment \
  --models claude-haiku-5-5 claude-sonnet-5-5 \
  --runs 10 \
  --effort medium \
  --max-tokens 16000 \
  --dry-run \
  --out artifacts/member1-experiment-dry-run-001
```

From the repository root, activate the Python 3.11 environment and enter the key locally.
The key must never be pasted into chat, written to a file, or committed. First make six
pilot calls by using `--runs 1` and a new output directory. If the final prompt,
parameters, and parser remain unchanged, the six records still remain excluded pilots.
The formal dataset is always generated in a fresh experiment directory.

```bash
source .venv/bin/activate
read -s "ANTHROPIC_API_KEY?Anthropic API key: "
export ANTHROPIC_API_KEY
printf '\n'
security-eval generate-experiment \
  --models claude-haiku-5-5 claude-sonnet-5-5 \
  --runs 1 \
  --effort medium \
  --max-tokens 16000 \
  --out artifacts/member1-pilot-001
unset ANTHROPIC_API_KEY
```

The full experiment uses the same command with `--runs 10` in a new output directory.
Success requires `manifest.json` to report `complete`, 60 unique candidate IDs, and all
60 records to report `generated`. A `generated` record proves only that the response
completed, parsed as Python, and contained the expected top-level function. It does not
prove functional correctness or security.

## Review and teammate delivery

Before sharing any artifact:

1. Confirm that `request.json` contains no credential and matches the fixed settings.
2. Confirm that each `response.json`, `completion.txt`, `code.py`, and `generation.json`
   exists and that the recorded code hash matches the candidate bytes.
3. Read the candidates without importing or executing them on the host.
4. Copy the reviewed batch into a tracked experiment directory or share it through the
   agreed team channel. The default `artifacts/` directory is intentionally Git-ignored.
5. Confirm that the manifest contains 30 candidates per model and ten per task-model pair.
6. Tell Members 2 and 3 to use the exact same `code.py` files and verify their hashes.

Start the integrated demo with `sql_delete_user`. Member 2 should run Bandit and the
custom AST rules. Member 3 should run functional and security tests only in the restricted
Docker environment. The team should report actual outcomes, including failures and tool
errors, without treating an empty finding list as proof of security.
