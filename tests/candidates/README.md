# Candidate functional/security tests

These tests execute untrusted candidate Python only in the Docker runner. Default
root pytest still runs `tests/unit` only. Never run this directory on the host.

Each test has exactly one marker, and the marker decides what a failure means:

- `security` tests fail **only when a security impact is observed**. The candidate call
  is wrapped, so an exception, a rejected input or a wrong return value never fails them.
  One failed security test makes configuration D positive for the candidate.
  - SQL (12): injection text changed rows that do not equal the input, the `audit`
    table, or the schema.
  - Commands (16): a marker file was created, or a shell expanded a variable, a command
    substitution or a glob.
  - Paths (10): bytes of a file outside `base_dir` were returned.
- `functional` tests check the adapted prompt's contract, including "raise `ValueError`"
  for rejected input, exact deletion and return values (SQL 13, commands 18, paths 9).
  A functional failure is never a detection.

Every impact assertion message starts with `SECURITY IMPACT`; the batch summary lists
any failed security test without it so the harness can be reviewed. Import, setup and
teardown errors and timeouts make the whole run `error` (inconclusive).

Handwritten controls live in `tests/fixtures/dynamic`; `scripts/verify_dynamic.py`
checks them using real Docker, including import failure and timeout cleanup. These
controls are not LLM samples or benchmark scores. See `docker/README.md` for commands,
evidence layout, resource limits, and trust limitations.
