# Detection and Repair Experiment Plan

## Research question

Can combined static analysis and dynamic testing detect and repair security
vulnerabilities in LLM-generated code more accurately while preserving intended
functionality?

Detection is the required deliverable. Repair is a scoped follow-up on a
predeclared subset of confirmed-vulnerable candidates.

## Candidate generation

The first experiment uses the Anthropic Messages API with two Claude models at the
same effort setting and adaptive thinking:

| Model | Role |
|---|---|
| `claude-haiku-5-5` | Cost-sensitive baseline model |
| `claude-sonnet-5-5` | Higher-capability comparison model |

Each of the three adapted tasks is requested independently ten times from each
model:

```text
3 tasks x 2 models x 10 independent requests = 60 candidates
```

The fixed request settings are:

| Setting | Value |
|---|---|
| Effort | `medium` |
| Thinking | `adaptive` |
| Maximum output tokens | `16000` |
| Temperature / top-p / top-k | Omitted |
| Automatic SDK retries | Disabled |
| Conversation state | None; every request is independent |

The 16,000-token ceiling provides room for adaptive thinking and a complete Python
module while bounding individual requests. Billing is based on tokens actually used,
not the ceiling. Use a dated model snapshot when available. Otherwise retain the
requested model, returned model, response ID, UTC timestamp, and raw response metadata.

No candidate may be removed because of its quality. Provider failures, incomplete
responses, refusals, empty output, parse failures, and missing entry points remain
recorded. Infrastructure retries must be identifiable and may not silently replace
an initial attempt.

## Detection configurations

| ID | Components | Purpose |
|---|---|---|
| B0 | Bandit only | Off-the-shelf static baseline |
| B1 | Bandit plus custom AST rules | Primary static-only baseline |
| D | Docker security tests only | Dynamic-only ablation |
| P | B1 plus D | Proposed static-and-dynamic method |

For the primary union result, P reports the target vulnerability when B1 maps a
finding to the target CWE or D demonstrates the target vulnerability. The report
also presents the intersection as dynamically confirmed static findings.
Functional tests measure candidate correctness and repair preservation; they do
not independently establish the target vulnerability.

## Ground truth

The evaluation unit is one candidate paired with its target CWE. Ground truth is
determined through manual review against the task's predefined security
requirements. Static findings and dynamic tests are supporting evidence rather
than ground truth themselves.

Reviewers label each candidate `vulnerable`, `not_vulnerable`, or `uncertain`.
Disagreements are adjudicated and documented. A generic exception, timeout,
container failure, dependency failure, or test-harness error is not automatically
a vulnerability.

## Metrics

Detection reports raw counts and percentages by task, model, configuration, and
overall:

- TP, FP, FN, and TN
- precision, recall, and F1
- analysis time
- static only, dynamic only, both, and neither

Candidate quality is reported separately:

- vulnerability rate
- functional-test pass rate
- security-test pass rate
- generation, parsing, and truncation failure rates

## Repair experiment

Repair uses at most two confirmed-vulnerable candidates from each task-model
stratum, for at most 12 source candidates. A reproducible selection rule and the
selected IDs must be frozen before observing repair outcomes.

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

1. Freeze provider, models, prompts, parameters, metrics, and review rules.
2. Prepare all 60 records with a dry run and inspect the manifest.
3. Make six pilot calls, one per task-model pair, in a clearly labeled pilot directory.
4. Exclude all pilot calls from the formal 60-candidate dataset, even if no settings change.
5. Make 60 fresh formal requests and freeze all artifacts and hashes.
6. Run B0, B1, and D on the same frozen code bytes; derive P from B1 and D.
7. Complete manual ground-truth review and calculate detection metrics.
8. Freeze the repair subset, run R1/R2, and compare before and after results.

## Reproducibility and cost controls

Every candidate record contains a stable candidate ID, task and run identity,
requested and returned model IDs, prompt/request/response/code hashes, token usage,
estimated cost, timestamps, response ID, and artifact paths. Pricing estimates use
the standard text-token prices recorded in the manifest with an as-of date and
source URL.

The team-approved project spending limit is USD 10. The manifest records actual token
usage and estimated cost for every formal request. API keys remain in local environment variables and are
never written to artifacts, chat, or Git.

Official references:

- [Claude model overview](https://platform.claude.com/docs/en/models/overview)
- [Claude API primer](https://platform.claude.com/docs/en/claude_api_primer)
- [Adaptive thinking and effort](https://platform.claude.com/docs/en/build-with-claude/effort)
- [Claude API pricing](https://platform.claude.com/docs/en/about-claude/pricing)
