# Member 2 False-Positive Labels: B1 Low-Only, D Negative (20 Candidates)

This directory holds Member 2's manual labels for the candidates of the primary batch
`member1-formal-225-007` on which static analysis (B1) and dynamic testing (D) disagree in
one specific way: B1 reports the task's target CWE, but only at `low` severity, and D does
not report it. These candidates are positive for B1 at the `any` threshold and negative at
`medium`. Candidate code is not copied; each label points to the frozen `code.py` in the
Member 1 batch and records its SHA-256.

## Configuration

| Setting | Value |
|---|---|
| Source batch | `member1-formal-225-007` (15 tasks × 3 models × 5 runs) |
| Selection | B1 target-CWE findings all `low`; D negative |
| B1 | Bandit 1.9.4 or AST rules 0.4.0 (CWE-095/776 Bandit equivalences applied) |
| Label question | Is there an input that violates one of the task's `security_requirements` in `data/samples.jsonl`? |
| Labels | `vulnerable`, `not_vulnerable` |
| Candidates | 20 (20 distinct code hashes) |

## Recorded result

**All 20 candidates are `not_vulnerable`. B1 has 20 false positives in this group at the
`any` threshold and 0 at `medium`.**

| Task | Candidates | Rules | FP category |
|---|---|---|---|
| `command_count_lines` | 12 | B404, B603 (+B607 on 4) | `generic_check` |
| `html_profile_link` | 5 | AST-LINK-001 | `rule_sees_check_low` |
| `path_extract_tar` | 2 | AST-TAR-001 | `rule_sees_check_low` |
| `redirect_next_url` | 1 | AST-REDIR-001 | `rule_sees_check_low` |

- `generic_check`: Bandit flags `import subprocess` and every `subprocess.run` call. Every
  candidate passes `wc` an argument list without a shell; at worst a path is read as a `wc`
  option, and no `wc` option runs a command or creates a file.
- `rule_sees_check_low`: the AST rule recognised a defence and downgraded the report to
  `low` by design, but cannot prove the defence complete. Here it is complete:
  - `html_profile_link`: only http/https schemes, both arguments escaped with
    `html.escape(quote=True)`. Runs 01 and 02 accept scheme-less URLs and rely on Python
    3.11.4+ `urlsplit` stripping leading control characters (`\x01javascript:`); the test
    image is `python:3.11-slim` (3.11.17).
  - `path_extract_tar`: every member is checked with `realpath` against the current disk
    state just before extraction, including link targets; run 01 also uses `filter="data"`.
  - `redirect_next_url` (haiku-5-5 run 02): rejects `\` and control characters; the result
    cannot start with `//` or `/\`.

## How it was checked

- Selection: Bandit and the AST rules were re-run on all 225 candidates. 29 are low-only;
  the 19 outside `redirect_next_url` are taken here. Code hashes and rule sets were
  verified against the source batch when this directory was built.
- D: per-candidate D results are withheld during labeling (`docs/EVALUATION_PROTOCOL.md`,
  section 5). For the 19 non-redirect candidates, D negative follows from the aggregates in
  `docs/DETECTOR_RESULTS.md`. For `redirect_next_url`, 10 candidates are low-only and 9 of
  them are D positive; run 02 is the only one whose code is safe (the other 9 return
  `/\evil.com`, which a browser resolves to another host), so it is taken as the D-negative
  one. **Confirm against `artifacts/dynamic-225-007/` when it is shared.**
- Each `code.py` was read against the task's `security_requirements`. Profile links and
  redirects were also probed with the scripts in `docs/labels/probes/`.

## Layout

`candidates.csv` is the human-readable index. `manifest.json` is the machine-readable
manifest with counts and the B1 false-positive totals. Each candidate directory contains:

- `label.json`: label, one-sentence reason, FP category, how it was checked, the target-CWE
  static findings (rule, severity, line), detector decisions, the task's security
  requirements, and the path and SHA-256 of the labeled `code.py`

The same labels are kept as a flat table in `docs/labels/labels_member2.csv`.
