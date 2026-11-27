# Evaluation protocol — DRAFT for team review

Status: proposed by Member 2; extends `docs/EXPERIMENT_PLAN.md` and uses its configuration
names. Generated candidates are archived under `experiments/`. Member 3 has run the Docker
tests on the primary batch locally; those results are not in the repository (`artifacts/`
is Git-ignored). **No static results on candidates or metrics exist yet.** Fix the
remaining decisions before looking at further results, and record later changes under
"Change log".

## 1. Why the comparison changes

A union of detectors can only add detections, so P-union always reports at least as many
pairs as B1. More detections are therefore expected, not evidence. The same is true of B0
vs. B1. Instead of asking "is the hybrid better?", we measure **what each approach reports
that the other misses, and how many static alerts no dynamic test confirms**, under two
defined fusion rules.

There is no manual ground truth (section 5). A dynamic security test fails only when it
observes a security impact, so a D positive is treated as a **confirmed** vulnerability.
Metrics are therefore stated relative to D, not as absolute precision or recall.

## 2. Research questions

- **RQ1 Complementarity:** How many dynamically confirmed vulnerabilities does static analysis
  also report, and how many does it miss? How many static alerts have no dynamic
  confirmation? (Same split for AST rules vs. Bandit.)
- **RQ2 Cost:** How many unconfirmed static alerts does each static configuration produce, and
  how many does adding AST rules to Bandit add?
- **RQ3 Fusion:** How do P-union (every pair either approach reports) and P-confirmed (static
  alerts confirmed by a dynamic test) differ in the number of pairs they report?
- **RQ4 Repair (Stage 2):** Does static + dynamic feedback produce better repairs than
  static-only feedback? As in the experiment plan, this follows the detection results.

## 3. Dataset

`data/samples.jsonl` defines 15 tasks, one target CWE each; the original 3 tasks and 8 pilot
tasks are in `data/extra_samples.jsonl`. Model-facing prompts state only the functional
contract; each task's `security_requirements` are withheld from the model and used for
testing. No candidate is removed because of its quality.

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
batches (276 IDs repeat). `metrics` and `dynamic` reject duplicate IDs, so run
them once per batch. This does not affect the primary batch on its own; pooling batches
would first need the batch name in the ID.

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

## 5. Reference without manual labels

The team does not label candidates manually. The reference is the dynamic result:

- **Confirmed vulnerable:** D positive, meaning a security test observed an impact that
  violates the task's `security_requirements` in `data/samples.jsonl`.
- **No confirmation:** D negative. The tests did not observe an impact; this does **not**
  establish that the candidate is secure.
- **Unknown:** D inconclusive or `no_test`. These pairs are counted and excluded from every
  metric that needs D.

Consequences: D cannot be evaluated against itself, so D has no precision or recall here; a
static alert without confirmation is "unconfirmed", not a proven false positive; and a
vulnerability that neither approach reports is invisible. Section 10 lists these limits.

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

Computed per configuration, per static threshold, overall and by task and model. Raw counts
are always shown; `n/a` means the denominator is zero.

- **Reported pairs:** how many pairs each configuration (B0, AST, B1, D, P-union, P-confirmed)
  reports, and how many it cannot decide.
- **Static vs. dynamic agreement** on pairs both decided: both, static only, dynamic only,
  neither.
- **Confirmation rate** of a static configuration: share of its alerts that D confirms
  (both ÷ static positive).
- **Coverage of confirmed vulnerabilities** by a static configuration: share of D positives it
  also reports (both ÷ D positive).
- **Unconfirmed alerts:** static-only pairs, per configuration; B0→B1 shows how many AST adds.
- **Bandit vs. AST agreement:** both, Bandit only, AST only, neither.
- **Coverage and quality:** dynamic outcomes by task, functional outcomes, share of
  candidates with a confirmed vulnerability, distinct code files, generation failures,
  analysis time.
- **Disagreement review:** a description of typical static-only and dynamic-only cases by
  rule and task, from the evidence the tools record.
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
| Member 2 | Metrics tooling; static results; disagreement review |
| Member 3 | Docker results for every 225-007 candidate (`pytest-docker.json`), shared with the team |

## 10. Known limitations

- 15 tasks and a few Claude models do not generalize to LLM-generated code in general.
- There is no independent ground truth. Every metric is relative to D, so D's own misses
  and false alarms cannot be measured, and vulnerabilities that neither approach reports are
  not counted anywhere.
- D is only as strong as each task's tests: a security test that never triggers the
  vulnerable path makes D miss it, and a static alert on that path then looks unconfirmed.
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
   pooling it with 225-007 would first need the batch name in the candidate ID.
2. Whether to add `Insecure_code` anchors for tasks with too few confirmed vulnerabilities.
3. The repair subset: per-stratum limit and total number of source candidates for 45
   task-model strata (`docs/EXPERIMENT_PLAN.md`).

## Change log

- Draft created by Member 2.
- Aligned with `docs/EXPERIMENT_PLAN.md`: names, 60-candidate dataset and `uncertain` label.
- Updated for the 15-task design: archived batches, dataset decision, equivalent Bandit rules,
  hardening checks, rule set 0.4.0 and limitations.
- Recorded `member1-formal-225-007` as the primary batch, how it was chosen, the shared
  dynamic results and the frozen components.
- Removed manual labeling: the dynamic result is the reference, and metrics are stated
  relative to it.
