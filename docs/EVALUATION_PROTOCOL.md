# Evaluation protocol — DRAFT for team review

Status: proposed by Member 2; extends `docs/EXPERIMENT_PLAN.md` and uses its configuration
names. Generated candidates are archived under `experiments/`. Member 3 has run the Docker
tests on the primary batch locally; those results are not in the repository (`artifacts/`
is Git-ignored). **No labels, static results on candidates or metrics exist yet.** Fix the
remaining decisions before looking at further results, and record later changes under
"Change log".

## 1. Why the comparison changes

A union of detectors can only add detections, so P-union can never have lower recall than
B1. A recall gain is therefore expected, not evidence. The same is true of B0 vs. B1.
Instead of asking "is the hybrid better?", we measure **what each approach finds that the
other misses, and at what false-positive cost**, under two defined fusion rules.

## 2. Research questions

- **RQ1 Complementarity:** How many true vulnerabilities does dynamic testing find that
  static analysis misses, and vice versa? (Same question for AST rules vs. Bandit.)
- **RQ2 Cost:** How many false positives does each approach produce, and how many does
  adding the other approach add?
- **RQ3 Fusion:** What is the precision/recall trade-off between P-union (maximum recall)
  and P-confirmed (static alert confirmed by a dynamic test)?
- **RQ4 Repair (Stage 2):** Does static + dynamic feedback produce better repairs than
  static-only feedback? As in the experiment plan, this follows the detection results.

## 3. Dataset

`data/samples.jsonl` defines 15 tasks, one target CWE each; the original 3 tasks and 8 pilot
tasks are in `data/extra_samples.jsonl`. Model-facing prompts state only the functional
contract; each task's `security_requirements` are withheld from the model and used for
testing and labeling. No candidate is removed because of its quality.

Seven generation batches are archived, one directory each under `experiments/`:

| Batch | Tasks | Models | Effort | Candidates (generated) |
|---|---|---|---|---|
| `pilot-probes-001` | 11 pilot | Haiku 5.5, Sonnet 5.5 | medium | 66 (63) |
| `member1-formal-60-002` | original 3 | Haiku 5.5, Sonnet 5.5 | medium | 60 (60) |
| `member1-formal-150-003` | 15 | Haiku 5.5, Sonnet 5.5 | medium | 150 (148) |
| `member1-formal-160-004` | 10 | Haiku 5.5, Sonnet 5.5 | medium | 160 (159) |
| `member1-formal-160-005` | 10 | Haiku 4.5, Haiku 5.5 | none | 160 (160) |
| `member1-sonnet46-80-006` | 10 | Sonnet 4.6 | none | 80 (80) |
| `member1-formal-225-007` | 15 | Haiku 4.5, Sonnet 4.6, Haiku 5.5 | none | 225 (225) |

**Primary experiment: `member1-formal-225-007`** (15 tasks × 3 models × 5 independent
requests = 225 candidates, 138 distinct code files). Requests send no thinking or effort
fields. Member 3 recorded this choice in the 2026-11-20 change summary; all detection
results are computed on this batch. The other six batches are not part of the primary
results; whether any is reported as supplementary is open decision 1. Pilot batches are
always excluded.

**How the dataset was chosen, which the report must disclose.** The design changed after
early outputs had been observed. The first candidates from the planned models passed almost
all security tests, so the task set was expanded to 15 tasks that are easier to get wrong.
Further batches were generated with other models and without thinking, and 225-007 was
adopted after Member 3 had seen dynamic test results. A dataset with no vulnerable
candidates cannot compare detectors, so this was a reasonable step. However, it means that
the task and batch selection was not blind to outcomes. From this point on, the dataset,
rules and tests stay frozen: none of them may be changed because of detection results
(section 8).

Candidate IDs combine task, model and run number only, so the same ID appears in several
batches (276 IDs repeat). `metrics`, `label-sheet` and `dynamic` reject duplicate IDs, so run
them once per batch. This does not affect the primary batch on its own; pooling batches
would first need the batch name in the ID or label key.

Optional known-positive anchors: SecurityEval `Insecure_code` adapted to our signatures, if
a task has too few vulnerable candidates. These are not LLM output and are always reported
separately.

## 4. Unit of analysis

The unit is one **(candidate, target CWE)** pair. Static tools report lines and dynamic tests
report outcomes, so both are reduced to a decision per pair. Decisions join by `sample_id`
and `code_sha256`.

- **Static positive:** at least one finding with the target CWE at or above the threshold.
  CWE comes from Bandit's `issue_cwe` or the AST rule. Bandit files some checks under a
  broader CWE, so `EQUIVALENT_RULES` in `evaluation.py` also counts `B307`/`B102` for CWE-095
  and the XML parser checks for CWE-776. Both thresholds are always reported:
  `any` (includes generic checks such as B404, which fires on importing `subprocess`) and
  `medium` (severity medium or high).
- **Dynamic positive:** at least one `security` test failed. Security tests fail only on an
  observed impact. Functional failures do not count, and `hardening` checks (rejections the
  prompt does not ask for) are reported separately by `security-eval dynamic` and do not count.
- **Inconclusive:** an analyzer that did not complete, or security tests that were all
  skipped. A candidate with no dynamic record is `no_test`, treated as inconclusive in
  metrics and shown separately under coverage. Neither counts as "not detected".
- Findings for other CWEs do not affect these decisions.

## 5. Ground truth

1. Two reviewers independently label each pair `vulnerable`, `not_vulnerable` or `uncertain`
   against the criterion below. **First-pass labels use the code only, with no detector
   output or test result**, so labels do not favor a detector
   (`security-eval label-sheet`).
2. `security-eval merge-labels` reports initial agreement and leaves disagreements blank.
   Adjudicate them in writing; tool outputs may be consulted at this stage only.
3. `uncertain` and blank pairs are excluded and counted.

Per-task pass counts from the dynamic run on 225-007 have already been shared within the team.
Reviewers must not look at per-candidate detector or test output before their first-pass
labels are complete. Record that the aggregate counts were known.

The labeling criterion for each task is its `security_requirements` entry in
`data/samples.jsonl`: label a pair `vulnerable` when an input can violate one of them. For
example, `sql_list_users` is vulnerable when an input value can change the structure of the
executed SQL.

## 6. Configurations

| Name | Pair is positive when |
|---|---|
| B0 | Bandit is positive |
| AST | A custom rule is positive (reported for complementarity only) |
| B1 | Bandit OR AST is positive |
| D | Dynamic is positive |
| P-union | B1 OR D (the plan's primary P) |
| P-confirmed | B1 AND D (dynamically confirmed static findings) |

If one input is inconclusive, a fusion decision is made only when the other input settles
it: P-union is positive if B1 is positive; P-confirmed is negative if B1 is negative.

## 7. Metrics

Computed per configuration, per threshold, overall and by task and model. Raw counts are
always shown; `n/a` means the denominator is zero.

- TP, FP, FN, TN, precision, recall, F1, false-positive rate, analysis time.
- **Complementarity:** static only, dynamic only, both, neither, separately for vulnerable
  and not-vulnerable pairs (false positives per approach); the same split for B0 vs. AST.
- **Fusion:** B0→B1, B1→P-union and B1→P-confirmed changes in TP, FP, precision and recall.
  Each comparison uses only rows that both configurations decided.
- **Coverage and quality:** dynamic outcomes by task, functional outcomes, vulnerability rate,
  distinct code files, generation failures.
- **Error analysis:** B1 false positives and negatives, categorized manually.
- **Repair (RQ4):** as defined in the experiment plan, evaluated after the detection results.

With at most a few hundred pairs per batch and 10 to 15 per task and model, results are
descriptive; we make no claims of statistical significance.

## 8. Fixed before running

Frozen from now on: the primary batch (`member1-formal-225-007`), Bandit version and flags
(`bandit 1.9.4`, `--ignore-nosec`), AST rule set `0.4.0`, `EQUIVALENT_RULES`, the candidate and
hardening tests, and the Docker image. Every result records these, plus models and parameters.
If anything changes after results are seen, re-run all candidates, report both versions and
add a change-log entry.

## 9. Responsibilities

| Owner | Task |
|---|---|
| Member 1 | Frozen generation batches and their manifests; explain each batch's purpose |
| Member 2 | Metrics tooling; static results; error analysis; coordinate labeling |
| Member 3 | Docker results for every 225-007 candidate (`pytest-docker.json`), shared with the team |
| All | Two independent labels per pair; adjudication |

## 10. Known limitations

- 15 tasks and a few Claude models do not generalize to LLM-generated code in general.
- Ground truth is manual and can be wrong; agreement is reported.
- D is only as strong as each task's tests: a security test that never triggers the
  vulnerable path makes D miss it.
- The tasks and the primary batch were chosen after early test outcomes had been seen
  (section 3), so the share of vulnerable candidates reflects that choice, not how often
  these models write insecure code in general.
- AST rules were designed for these tasks, which may favor them compared with Bandit. The
  rule set 0.4.0 rules for the three tasks promoted from the pilot were written after pilot
  candidates had been read (see `docs/STATIC_ANALYSIS.md`). Rule tests are hand-written and
  are not experiment results.
- Bandit has no check for several target CWEs (for example CWE-117, CWE-209, CWE-601), so B0
  finds nothing on those tasks by construction.
- Identical candidates are counted separately; `distinct_code` shows how many differ.

## 11. Open decisions

1. Whether any batch other than 225-007 is reported as supplementary, and for what question;
   pooling it with 225-007 would first need the batch name in the candidate ID or label key.
2. Whether to add `Insecure_code` anchors for tasks with too few vulnerable candidates.
3. Who labels which of the 225 candidates (138 distinct code files).
4. `docs/EXPERIMENT_PLAN.md` and the README still describe the 3-task, 60-candidate design;
   Members 1 and 3 should update them to match this section.

## Change log

- Draft created by Member 2.
- Aligned with `docs/EXPERIMENT_PLAN.md`: names, 60-candidate dataset and `uncertain` label.
- Updated for the 15-task design: archived batches, dataset decision, equivalent Bandit rules,
  hardening checks, rule set 0.4.0 and limitations.
- Recorded `member1-formal-225-007` as the primary batch, how it was chosen, the shared
  dynamic results and the frozen components.
