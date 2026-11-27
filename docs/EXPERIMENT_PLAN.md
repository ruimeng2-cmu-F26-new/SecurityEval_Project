# Detection and Repair Experiment Plan

## Research question

Can combined static analysis and dynamic testing detect and repair security
vulnerabilities in LLM-generated code more accurately while preserving intended
functionality?

Detection is the required deliverable. Repair is a scoped follow-up on a
predeclared subset of confirmed-vulnerable candidates.

## Candidate generation

The primary experiment is the archived batch `experiments/member1-formal-225-007`:

```text
15 tasks x 3 models x 5 independent requests = 225 candidates (138 distinct code files)
```

| Model | Requested ID |
|---|---|
| Claude Haiku 4.5 | `claude-haiku-4-5-20251001` |
| Claude Sonnet 4.6 | `claude-sonnet-4-6` |
| Claude Haiku 5.5 | `claude-haiku-5-5` |

The fixed request settings are:

| Setting | Value |
|---|---|
| Thinking and effort fields | Not sent (`--effort none`); each model's default applies |
| Maximum output tokens | `16000` |
| Temperature / top-p / top-k | Omitted |
| Automatic SDK retries | Disabled |
| Conversation state | None; every request is independent |

All 225 records have status `generated`; the manifest's estimated cost is USD 0.0364. The 15
tasks and their target CWEs are in `data/samples.jsonl`; the original 3 tasks and the pilot
tasks are in `data/extra_samples.jsonl`.

**How this design was reached.** The plan started with 3 tasks, `claude-haiku-5-5` and
`claude-sonnet-5-5`, adaptive thinking and medium effort (`member1-formal-60-002`). Those
candidates passed almost all security tests, so a dataset without vulnerable candidates
could not compare detectors. The task set was expanded to 15 tasks that are easier to get
wrong, further batches were generated with other models and without thinking, and 225-007
was adopted after its dynamic test results had been seen. The report must disclose that the
task and batch selection was not blind to outcomes. The other batches under `experiments/`
are not part of the primary results; `docs/EVALUATION_PROTOCOL.md` lists them.

Use a dated model snapshot when available. Otherwise retain the requested model, returned
model, response ID, UTC timestamp, and raw response metadata.

No candidate may be removed because of its quality. Provider failures, incomplete
responses, refusals, empty output, parse failures, and missing entry points remain
recorded. Infrastructure retries must be identifiable and may not silently replace
an initial attempt.

### Prompt policy

The frozen model-facing prompts describe the function signature and functional boundary
only. They do not reveal security requirements, attack strings, or defensive implementation
instructions. The separate `security_requirements` fields are used by the test harness and never
included in a generation request. Prompt hashes
are frozen in the harness tests before pilot or formal generation begins.

## Detection configurations

| ID | Components | Purpose |
|---|---|---|
| B0 | Bandit only | Off-the-shelf static baseline |
| B1 | Bandit plus custom AST rules | Primary static-only baseline |
| D | Docker security tests only | Dynamic-only ablation and reference |
| P-union | B1 OR D | Every pair either approach reports |
| P-confirmed | B1 AND D | Static findings confirmed by a dynamic test |

Functional tests measure candidate correctness and repair preservation; they do not
establish the target vulnerability. Hardening checks are reported separately and affect
neither D nor the functional outcome.

## Reference: no manual labels

The evaluation unit is one candidate paired with its target CWE. There is no manual
ground-truth review. A security test fails only when it observes an impact that violates
the task's `security_requirements`, so a D positive is treated as a confirmed vulnerability.
A D negative is not proof of security, and a generic exception, timeout, container failure,
dependency failure, or test-harness error is inconclusive, not a vulnerability.

Because D is the reference, D's own misses and false alarms cannot be measured, a static
finding without a D positive is unconfirmed rather than a proven false positive, and
vulnerabilities that neither approach reports are not counted.

## Metrics

Detection reports raw counts and percentages per static threshold (`any`, `medium`), by
task, model, and configuration, and overall (definitions in `docs/EVALUATION_PROTOCOL.md`):

- pairs reported, not reported, and undecided by each configuration
- static vs. dynamic: both, static only (unconfirmed), dynamic only, and neither
- confirmation rate: share of static alerts that D confirms
- coverage of confirmed vulnerabilities: share of D positives that static analysis reports
- Bandit vs. AST agreement
- analysis time

Candidate quality is reported separately:

- share of candidates with a confirmed vulnerability (D positive)
- functional-test pass rate
- hardening-check pass rate
- generation, parsing, and truncation failure rates

## Repair experiment

Repair uses confirmed-vulnerable candidates (D positive) from 225-007. With 45 task-model
strata, the per-stratum limit and the total number of source candidates must be fixed
again before repair starts (the earlier limit of 12 was for 3 tasks and 2 models). A
reproducible selection rule and the selected IDs must be frozen before observing repair
outcomes.

| ID | Feedback |
|---|---|
| R0 (optional) | General instruction to repair the security issue |
| R1 | Bandit and AST findings |
| R2 | Static findings plus dynamic-test evidence |

R1 and R2 use the same repair model, reasoning effort, prompt template, original
candidate, and output limit. Only the evidence differs. The proposed repair model
is `claude-sonnet-5-5` with adaptive thinking and medium effort. Detection remains the primary result;
the initial repair phase uses one attempt per condition and states that limitation.

Repair reports success rate, functional preservation, post-repair security-test
pass rate, residual static findings, and regressions.

## Execution order

1. Done: freeze provider, models, prompts, and parameters; generate and archive 225-007.
2. Done by Member 3 (results local, not in the repository): run D on 225-007.
3. Run B0 and B1 on the same frozen code bytes (`security-eval static`).
4. Join static and dynamic results and calculate detection metrics (`security-eval metrics`).
5. Describe typical static-only and dynamic-only cases from the recorded evidence.
6. Freeze the repair subset, run R1/R2, and compare before and after results.

## Reproducibility and cost controls

Every candidate record contains a stable candidate ID, task and run identity,
requested and returned model IDs, prompt/request/response/code hashes, token usage,
estimated cost, timestamps, response ID, and artifact paths. Pricing estimates use
the standard text-token prices recorded in the manifest with an as-of date and
source URL.

The team-approved project spending limit is USD 10. Each manifest records actual token
usage and estimated cost for every request. API keys remain in local environment variables and are
never written to artifacts, chat, or Git.

Official references:

- [Claude model overview](https://platform.claude.com/docs/en/models/overview)
- [Claude API primer](https://platform.claude.com/docs/en/claude_api_primer)
- [Adaptive thinking and effort](https://platform.claude.com/docs/en/build-with-claude/effort)
- [Claude API pricing](https://platform.claude.com/docs/en/about-claude/pricing)
