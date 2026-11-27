# B1 low-only reports that D did not confirm (Member 2)

Batch `member1-formal-225-007`. Scope: candidates where B1 reports the target CWE only at
`low` severity (so positive at the `any` threshold, negative at `medium`) and D is negative.
Table: [`labels_member2.csv`](labels_member2.csv), one row per candidate.

## Result

All 20 candidates (20 distinct code files) are `not_vulnerable`: no input violates the task's
`security_requirements`. **B1 has 20 false positives in this group, all at the `any`
threshold only;** they do not affect `medium`.

| Task | Candidates | Rules | FP category |
|---|---|---|---|
| `command_count_lines` | 12 | B404, B603 (+B607 on 4) | `generic_check` |
| `html_profile_link` | 5 | AST-LINK-001 | `rule_sees_check_low` |
| `path_extract_tar` | 2 | AST-TAR-001 | `rule_sees_check_low` |
| `redirect_next_url` | 1 | AST-REDIR-001 | `rule_sees_check_low` |

- `generic_check`: Bandit flags `import subprocess` and any `subprocess.run` call. Every
  candidate passes an argument list without a shell, so input cannot run a command.
- `rule_sees_check_low`: the AST rule recognised a defence and downgraded the report to `low`
  by design, but cannot prove the defence is complete. Here the defence is complete.

## How it was checked

- Static: re-ran `security-eval static` on `main`; 246 findings, same as
  `docs/DETECTOR_RESULTS.md`. 29 candidates are low-only.
- D: per-candidate dynamic results were not available. 19 rows are D-negative by the
  aggregates (their tasks have no D positive in the low-only group). For `redirect_next_url`,
  10 candidates are low-only and 9 of them are D positive; the judgments were made from the
  code without D, and exactly one (`claude-haiku-5-5__run_02`) is safe, so it is taken as the
  D-negative one. Confirm against `artifacts/dynamic-225-007/` when shared.
- Each `code.py` was read against `data/samples.jsonl`. Profile links and redirects were also
  probed with the scripts in [`probes/`](probes/); redirect outputs are resolved with Node's
  WHATWG `URL`, which treats `\` like `/` as browsers do.

## Notes for the other groups

- The other 9 low-only `redirect_next_url` candidates are vulnerable: `/\evil.com` (and
  `https://shop.example//evil.com` for two Sonnet 4.6 runs) leads the browser to another
  host. AST-REDIR-001 downgrades them to `low` because they parse the URL, which is why B1
  misses them at `medium`. This is relevant to the "D positive, B1 negative at medium" group.
- `html_profile_link` runs 01 and 02 are safe only because Python 3.11.4+ `urlsplit` strips
  leading control characters (`\x01javascript:`); on older Python they would be bypassable.
