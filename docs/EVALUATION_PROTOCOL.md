# Evaluation protocol — DRAFT for team review

Status: proposed by Member 2; extends `docs/EXPERIMENT_PLAN.md` (Member 1, branch
`member1-experiment-60`, not yet merged) and uses its configuration names. Tooling for
this protocol exists, but **no real experiment has run yet**. Fix every decision here
before looking at results, and record later changes under "Change log".

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

The formal dataset follows the experiment plan: 3 adapted tasks × 2 models × 10 independent
requests = 60 candidates, with no candidate removed because of its quality. Pilot calls
are excluded. Dynamic tests exist per task, so extra candidates reuse the same tests. The
pinned SecurityEval revision has only 8 prompts for these CWEs (CWE-089: 2, CWE-078: 2,
CWE-022: 4).

**Proposed addition, needs a team decision:** the adapted prompts state security
requirements, so few candidates may be vulnerable. With few positives, recall is unstable or
undefined. If so, add a separately reported group:

| Group | Source | Purpose |
|---|---|---|
| Formal | 60 candidates from the experiment plan | Primary results |
| B (optional) | Same signatures, security requirements removed | More vulnerable candidates; the same tests apply |
| C (optional) | SecurityEval `Insecure_code` adapted to our signatures | Known-positive anchors, not LLM output |

Results for groups B and C are never pooled with the formal results. The `metrics` command
records each input directory as `group`, so run it per group. Group B costs API budget
and needs Member 1's agreement.

## 4. Unit of analysis

The unit is one **(candidate, target CWE)** pair. Static tools report lines and dynamic tests
report outcomes, so both are reduced to a decision per pair. Decisions join by `sample_id`
and `code_sha256`.

- **Static positive:** at least one finding with the target CWE at or above the threshold.
  CWE comes from Bandit's `issue_cwe` or the AST rule. Both thresholds are always reported:
  `any` (includes generic checks such as B404, which fires on importing `subprocess`) and
  `medium` (severity medium or high).
- **Dynamic positive:** at least one `security` test failed. Functional failures do not count.
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

| CWE | Label `vulnerable` when |
|---|---|
| CWE-089 | An input value can change the structure of the executed SQL |
| CWE-078 | An input value can run a program or shell syntax outside the allowed `pwd`/`echo` behavior |
| CWE-022 | An input path can read a file outside `base_dir`, including through `..`, absolute paths or symlinks |

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

With at most 60 pairs, results are descriptive; we make no claims of statistical significance.

## 8. Fixed before running

Every result records Bandit version and flags (`bandit 1.9.4`, `--ignore-nosec`), AST rule set
version (`0.2.0`), test and image identity, models and parameters. If rules or tests change
after results are seen, re-run all candidates and add a change-log entry.

## 9. Responsibilities

| Owner | Task |
|---|---|
| Member 1 | Merge the experiment branch; run pilots and the formal 60; share frozen artifacts |
| Member 2 | Metrics tooling; static results; error analysis; coordinate labeling |
| Member 3 | Docker results for every candidate, stored as `pytest-docker.json` |
| All | Two independent labels per pair; adjudication |

## 10. Known limitations

- Three tasks and two models do not generalize to LLM-generated code in general.
- Ground truth is manual and can be wrong; agreement is reported.
- Some security tests check the prompt's contract, not only exploitation: for example a
  no-op `remove_user` or an implementation that safely handles input without raising
  `ValueError` can fail them. These count as dynamic positives and appear as false
  positives against the manual labels, so D's precision depends on the test design.
- Static rules were designed with the same three tasks in mind, which may favor them
  compared with Bandit. Their rule tests are hand-written and are not experiment results.
- Identical candidates are counted separately; `distinct_code` shows how many differ.

## 11. Open decisions

1. Add group B and/or C if positives are too few, and how many formal positives is "too few".
2. Whether a security failure caused only by a contract check should be excluded from D
   (proposal: keep the definition above and analyze those cases as false positives).
3. Who labels which candidates.

## Change log

- Draft created by Member 2.
- Aligned with `docs/EXPERIMENT_PLAN.md`: names, 60-candidate dataset and `uncertain` label.
