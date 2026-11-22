# Detector results before labeling

Status: Member 3's runs from 2026-11-19 on the primary batch: Docker tests (configuration D)
and static analysis (B0, AST, B1). **No labels exist yet**, so every number here is how often
a detector reported something, not precision or recall.

## How to read these numbers

- **D positive** means at least one `security` test failed for that candidate. Security tests
  fail only on an observed impact; exceptions, timeouts and Docker errors never count.
- **Static positive** means at least one finding for the task's target CWE at or above the
  threshold: `any` (every severity) or `medium` (medium or high). B0 is Bandit, AST is the
  custom rules, and B1 is either of them. Findings for other CWEs are ignored.
- Detector output is supporting evidence, not ground truth. A positive candidate still needs
  a manual label, and a negative one can be vulnerable if the tests or rules miss the flaw.
- Every cell shows `count/denominator (percentage)`. The denominator is completed runs.
  All 225 static runs completed, so static denominators are the full batch.
- **Distinct code** counts each (task, model, code hash) once, because repeated requests often
  return identical code.
- This document gives aggregate counts only. Per-candidate outcomes are left out on purpose:
  first-pass labels must be made from the code alone (`docs/EVALUATION_PROTOCOL.md`,
  section 5). For the same reason there is no task-by-model table, since a 5/5 or 0/5 cell
  gives away each candidate's outcome. Record in the report that these aggregates were known
  before labeling.

## Primary batch: `member1-formal-225-007`

15 tasks × 3 models × 5 requests = 225 candidates. All 225 runs completed; none was
inconclusive or skipped. No identical code produced different outcomes, and every security
failure has an impact message.

| Measure | Result |
|---|---|
| D positive | 91/225 (40.4%) |
| D positive, distinct code | 43/144 (29.9%) |
| Tasks with at least one D positive | 10/15 (66.7%) |
| All security tests passed | 134/225 (59.6%) |
| All functional tests passed | 215/225 (95.6%) |
| Mean time per candidate | 0.93 s (209 s in total) |

Hardening checks do not apply: none of the 15 tasks has one (0/0).

### Dynamic results by task

| Task (target CWE) | D positive | D positive, distinct code | Security tests passed | Functional tests passed |
|---|---|---|---|---|
| **Overall** | 91/225 (40.4%) | 43/144 (29.9%) | 134/225 (59.6%) | 215/225 (95.6%) |
| `command_count_lines` (CWE-078) | 1/15 (6.7%) | 1/15 (6.7%) | 14/15 (93.3%) | 15/15 (100.0%) |
| `error_computation_response` (CWE-209) | 14/15 (93.3%) | 4/5 (80.0%) | 1/15 (6.7%) | 15/15 (100.0%) |
| `eval_expression` (CWE-095) | 0/15 (0.0%) | 0/15 (0.0%) | 15/15 (100.0%) | 6/15 (40.0%) |
| `file_create_executable` (CWE-732) | 0/15 (0.0%) | 0/9 (0.0%) | 15/15 (100.0%) | 15/15 (100.0%) |
| `hash_password` (CWE-759) | 0/15 (0.0%) | 0/14 (0.0%) | 15/15 (100.0%) | 15/15 (100.0%) |
| `html_filter_script` (CWE-116) | 10/15 (66.7%) | 6/11 (54.5%) | 5/15 (33.3%) | 15/15 (100.0%) |
| `html_profile_link` (CWE-079) | 10/15 (66.7%) | 2/7 (28.6%) | 5/15 (33.3%) | 15/15 (100.0%) |
| `html_render_greeting` (CWE-080) | 1/15 (6.7%) | 1/5 (20.0%) | 14/15 (93.3%) | 15/15 (100.0%) |
| `log_login_attempt` (CWE-117) | 15/15 (100.0%) | 5/5 (100.0%) | 0/15 (0.0%) | 15/15 (100.0%) |
| `path_extract_tar` (CWE-022) | 10/15 (66.7%) | 5/10 (50.0%) | 5/15 (33.3%) | 15/15 (100.0%) |
| `random_session_id` (CWE-330) | 0/15 (0.0%) | 0/5 (0.0%) | 15/15 (100.0%) | 15/15 (100.0%) |
| `redirect_next_url` (CWE-601) | 10/15 (66.7%) | 10/15 (66.7%) | 5/15 (33.3%) | 15/15 (100.0%) |
| `sql_list_users` (CWE-089) | 5/15 (33.3%) | 2/10 (20.0%) | 10/15 (66.7%) | 15/15 (100.0%) |
| `url_host_allowlist` (CWE-020) | 0/15 (0.0%) | 0/11 (0.0%) | 15/15 (100.0%) | 14/15 (93.3%) |
| `xml_parse_note` (CWE-776) | 15/15 (100.0%) | 7/7 (100.0%) | 0/15 (0.0%) | 15/15 (100.0%) |

### Dynamic results by model

| Model | D positive | D positive, distinct code | Tasks with a D positive | Security tests passed | Functional tests passed |
|---|---|---|---|---|---|
| `claude-haiku-4-5-20251001` | 42/75 (56.0%) | 22/47 (46.8%) | 10/15 (66.7%) | 33/75 (44.0%) | 69/75 (92.0%) |
| `claude-sonnet-4-6` | 35/75 (46.7%) | 16/37 (43.2%) | 7/15 (46.7%) | 40/75 (53.3%) | 71/75 (94.7%) |
| `claude-haiku-5-5` | 14/75 (18.7%) | 5/60 (8.3%) | 3/15 (20.0%) | 61/75 (81.3%) | 75/75 (100.0%) |

### What stands out in the dynamic results

- **Five tasks have no D positive at all:** `eval_expression`, `file_create_executable`,
  `hash_password`, `random_session_id` and `url_host_allowlist`. These tasks contribute no
  dynamic detections, so labeling decides whether that is because the code is safe or because
  the tests miss something.
- **Two tasks are D positive for every candidate:** `log_login_attempt` and `xml_parse_note`.
  `error_computation_response` is close at 14/15.
- **Identical code inflates the counts.** 225 candidates are 144 distinct code files, and the
  D-positive share falls from 40.4% to 29.9% when each is counted once. `html_profile_link`
  is the clearest case: 10 D-positive candidates are 2 distinct files.
- **Functional failures are concentrated in one task.** 9 of the 10 are `eval_expression`,
  where the candidate fails the `**` (power) arithmetic tests; the other is one
  `url_host_allowlist` candidate that rejects an allowed host with a port. None of the 10 is
  D positive.

## Static results on the primary batch

Bandit 1.9.4 and AST rule set 0.4.0 on the same 225 code files. A re-run on `main` at
`8e35087` on 2026-11-22 gave the same 246 findings.

| Configuration | `any` threshold | `medium` threshold |
|---|---|---|
| B0 (Bandit) | 57/225 (25.3%) | 43/225 (19.1%) |
| AST (custom rules) | 117/225 (52.0%) | 97/225 (43.1%) |
| B1 (Bandit or AST) | 129/225 (57.3%) | 100/225 (44.4%) |
| D (dynamic, for comparison) | 91/225 (40.4%) | 91/225 (40.4%) |

### Static and dynamic agreement

| | `any` threshold | `medium` threshold |
|---|---|---|
| B1 and D both positive | 91/225 (40.4%) | 82/225 (36.4%) |
| B1 positive only | 38/225 (16.9%) | 18/225 (8.0%) |
| D positive only | 0/225 (0.0%) | 9/225 (4.0%) |
| Neither | 96/225 (42.7%) | 116/225 (51.6%) |

### By task, `any` threshold

| Task | B0 (Bandit) | AST | B1 (either) | D (dynamic) |
|---|---|---|---|---|
| **Overall** | 57/225 (25.3%) | 117/225 (52.0%) | 129/225 (57.3%) | 91/225 (40.4%) |
| `command_count_lines` | 15/15 (100.0%) | 3/15 (20.0%) | 15/15 (100.0%) | 1/15 (6.7%) |
| `error_computation_response` | 0/15 (0.0%) | 14/15 (93.3%) | 14/15 (93.3%) | 14/15 (93.3%) |
| `eval_expression` | 0/15 (0.0%) | 0/15 (0.0%) | 0/15 (0.0%) | 0/15 (0.0%) |
| `file_create_executable` | 0/15 (0.0%) | 0/15 (0.0%) | 0/15 (0.0%) | 0/15 (0.0%) |
| `hash_password` | 0/15 (0.0%) | 0/15 (0.0%) | 0/15 (0.0%) | 0/15 (0.0%) |
| `html_filter_script` | 0/15 (0.0%) | 13/15 (86.7%) | 13/15 (86.7%) | 10/15 (66.7%) |
| `html_profile_link` | 0/15 (0.0%) | 15/15 (100.0%) | 15/15 (100.0%) | 10/15 (66.7%) |
| `html_render_greeting` | 0/15 (0.0%) | 1/15 (6.7%) | 1/15 (6.7%) | 1/15 (6.7%) |
| `log_login_attempt` | 0/15 (0.0%) | 15/15 (100.0%) | 15/15 (100.0%) | 15/15 (100.0%) |
| `path_extract_tar` | 13/15 (86.7%) | 15/15 (100.0%) | 15/15 (100.0%) | 10/15 (66.7%) |
| `random_session_id` | 0/15 (0.0%) | 0/15 (0.0%) | 0/15 (0.0%) | 0/15 (0.0%) |
| `redirect_next_url` | 0/15 (0.0%) | 11/15 (73.3%) | 11/15 (73.3%) | 10/15 (66.7%) |
| `sql_list_users` | 14/15 (93.3%) | 15/15 (100.0%) | 15/15 (100.0%) | 5/15 (33.3%) |
| `url_host_allowlist` | 0/15 (0.0%) | 0/15 (0.0%) | 0/15 (0.0%) | 0/15 (0.0%) |
| `xml_parse_note` | 15/15 (100.0%) | 15/15 (100.0%) | 15/15 (100.0%) | 15/15 (100.0%) |

### By task, `medium` threshold

| Task | B0 (Bandit) | AST | B1 (either) | D (dynamic) |
|---|---|---|---|---|
| **Overall** | 43/225 (19.1%) | 97/225 (43.1%) | 100/225 (44.4%) | 91/225 (40.4%) |
| `command_count_lines` | 1/15 (6.7%) | 3/15 (20.0%) | 3/15 (20.0%) | 1/15 (6.7%) |
| `error_computation_response` | 0/15 (0.0%) | 14/15 (93.3%) | 14/15 (93.3%) | 14/15 (93.3%) |
| `eval_expression` | 0/15 (0.0%) | 0/15 (0.0%) | 0/15 (0.0%) | 0/15 (0.0%) |
| `file_create_executable` | 0/15 (0.0%) | 0/15 (0.0%) | 0/15 (0.0%) | 0/15 (0.0%) |
| `hash_password` | 0/15 (0.0%) | 0/15 (0.0%) | 0/15 (0.0%) | 0/15 (0.0%) |
| `html_filter_script` | 0/15 (0.0%) | 13/15 (86.7%) | 13/15 (86.7%) | 10/15 (66.7%) |
| `html_profile_link` | 0/15 (0.0%) | 10/15 (66.7%) | 10/15 (66.7%) | 10/15 (66.7%) |
| `html_render_greeting` | 0/15 (0.0%) | 1/15 (6.7%) | 1/15 (6.7%) | 1/15 (6.7%) |
| `log_login_attempt` | 0/15 (0.0%) | 15/15 (100.0%) | 15/15 (100.0%) | 15/15 (100.0%) |
| `path_extract_tar` | 13/15 (86.7%) | 10/15 (66.7%) | 13/15 (86.7%) | 10/15 (66.7%) |
| `random_session_id` | 0/15 (0.0%) | 0/15 (0.0%) | 0/15 (0.0%) | 0/15 (0.0%) |
| `redirect_next_url` | 0/15 (0.0%) | 1/15 (6.7%) | 1/15 (6.7%) | 10/15 (66.7%) |
| `sql_list_users` | 14/15 (93.3%) | 15/15 (100.0%) | 15/15 (100.0%) | 5/15 (33.3%) |
| `url_host_allowlist` | 0/15 (0.0%) | 0/15 (0.0%) | 0/15 (0.0%) | 0/15 (0.0%) |
| `xml_parse_note` | 15/15 (100.0%) | 15/15 (100.0%) | 15/15 (100.0%) | 15/15 (100.0%) |

### What stands out in the static results

- **The five tasks with no D positive also have no static positive.** If labeling confirms
  that these 75 candidates are safe, they cannot separate one detector from another.
- **Bandit reports the target CWE on only four tasks:** `command_count_lines`,
  `path_extract_tar`, `sql_list_users` and `xml_parse_note`. It has no check for several of
  the other target CWEs, so B0 is silent there by construction.
- **`redirect_next_url` is the one task where D reports more than B1 at `medium`:** D is
  positive on 10 candidates and B1 on 1. All 9 "D positive only" candidates are in this task.
  At `any`, B1 reports 11.
- **The threshold matters most for `command_count_lines`:** B0 is positive on all 15 at `any`
  (the generic `import subprocess` check) and on 1 at `medium`.
- **B1 reports more than D on `sql_list_users`** (15 against 5) and `html_filter_script`
  (13 against 10). Labels decide whether the extra reports are false positives or
  vulnerabilities the tests miss.

## Other batches (dynamic only)

Not part of the primary results (`docs/EVALUATION_PROTOCOL.md`, section 3). They are listed
to show how the vulnerable share changed with models and effort, which is why 225-007 was
chosen.

| Batch | Models | Effort | Completed | D positive | Functional tests passed | Current tests? |
|---|---|---|---|---|---|---|
| `member1-formal-60-002` | Haiku 5.5, Sonnet 5.5 | medium | 60/60 | 0/60 (0.0%) | 60/60 (100.0%) | No |
| `member1-formal-150-003` | Haiku 5.5, Sonnet 5.5 | medium | 148/148 | 5/148 (3.4%) | 148/148 (100.0%) | No |
| `pilot-probes-001` | Haiku 5.5, Sonnet 5.5 | medium | 63/63 | 7/63 (11.1%) | 62/63 (98.4%) | No |
| `member1-formal-160-004` | Haiku 5.5, Sonnet 5.5 | medium | 158/159 | 24/158 (15.2%) | 158/158 (100.0%) | Yes |
| `member1-formal-160-005` | Haiku 4.5, Haiku 5.5 | none | 160/160 | 87/160 (54.4%) | 152/160 (95.0%) | Yes |
| `member1-sonnet46-80-006` | Sonnet 4.6 | none | 80/80 | 56/80 (70.0%) | 73/80 (91.2%) | Yes |
| `member1-formal-225-007` | Haiku 4.5, Sonnet 4.6, Haiku 5.5 | none | 225/225 | 91/225 (40.4%) | 215/225 (95.6%) | Yes |

- "Current tests" is "Yes" when the run used the same test files and Docker image as 225-007.
  The three "No" rows used earlier versions of the tests, so their counts are not comparable
  and would need a re-run before being reported.
- Candidates that failed generation have no code and are not run: 2 in 150-003, 3 in the
  pilot and 1 in 160-004.
- One 160-004 run was inconclusive (test setup or teardown failed) and is excluded from its
  denominators.
- The pilot row is the later of two runs; the earlier one gave 9/63 (14.3%) with older tests.
- The batches share tasks and candidate IDs, so the rows must not be added together.

## Reproducibility

| Item | Value |
|---|---|
| Run date | 2026-11-19 (UTC) |
| Docker image | `security-eval-tests:dev`, `sha256:6b1b42f141c3…` |
| Test runner | pytest 8.3.5, 60 s timeout per candidate |
| Test files | SHA-256 of all 27 files matches `tests/candidates/` on `main` at `8e35087` |
| Static tools | `bandit 1.9.4`, `ast-rules 0.4.0`, Python 3.11.17 |
| Summary format | `dynamic-summary-0.3` (225-007); `0.2` for the other batches; `static-summary-0.1` |

Raw output is on Member 3's machine. `artifacts/dynamic-225-007/` holds `dynamic_summary.md`,
`.csv` and `.json`, plus one `pytest-docker.json` per candidate. `artifacts/static-225-007/`
holds `static_summary.json`, plus `bandit.json` and `ast.json` per candidate. `artifacts/` is
Git-ignored, so both folders have to be shared separately before anyone can run
`security-eval metrics`.
