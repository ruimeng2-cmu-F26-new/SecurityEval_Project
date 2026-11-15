# Member 3: isolated candidate execution

Build from the repository root (Docker Desktop/Engine must be running):

```bash
docker build -f docker/Dockerfile -t security-eval-tests:dev .
python scripts/verify_dynamic.py --out artifacts/dynamic-controls-001
```

The verification command executes fifteen **handwritten controls**, not model outputs,
and checks the expected D decision, functional outcome and container removal for each.
Use a fresh output path each time.

## Running configuration D on the frozen candidates

```bash
security-eval dynamic artifacts/<experiment-dir> --out artifacts/dynamic-001
```

The input is Member 1's experiment directory (or single run directories). Each candidate's
hash is checked against `generation.json` and the experiment `manifest.json`; records that
are not `generated` or do not match are listed under `skipped`, never executed. Output:

- `<candidate_id>/pytest-docker.json`: analysis contract, the file `security-eval metrics`
  reads through `--results`.
- `<candidate_id>/pytest-docker/`: report, stdout/stderr, Docker commands, environment.
- `dynamic_summary.json`, `.md`, `.csv`: D decision and functional outcome per candidate,
  counts overall and by task and model, image ID and test hashes, identical code with
  different outcomes, and security failures lacking an impact message.

D is `yes` when at least one `security` test failed, `no` when security tests ran and none
failed, and `inconclusive` when the run did not complete. Security tests fail only on an
observed impact (see `tests/candidates/README.md`), so exceptions, timeouts, missing
dependencies and Docker or harness failures are never detections. D is supporting
evidence for the manual review, not ground truth. The command exits nonzero if any
candidate was skipped or inconclusive; rerun into a new directory and keep both.

A single candidate can still be evaluated with all three tools:

```bash
security-eval evaluate artifacts/sql-live-001 --out artifacts/sql-analysis-001
```

`DockerPytestAnalyzer(evidence_dir=...)` enables execution; without an evidence
directory it explicitly returns `not_run`. The pipeline supplies that directory.
No Docker fallback executes candidates on the host. The pipeline runs Bandit, AST rules, and Docker testing. Infrastructure errors in
any adapter make the evaluate command return nonzero. Inspect each tool report;
`completed` does not imply that every test passed or that there are no findings.

The runner snapshots candidate bytes, verifies the hash, resolves the image to an
immutable local image ID, and never pulls an image during candidate execution. It
uses a non-root UID, read-only root/candidate mount, no network, dropped capabilities,
no-new-privileges, bounded tmpfs, CPU/memory/PID/descriptor limits and bounded Docker
logs. Only the candidate snapshot is mounted; no repo, credentials, or Docker socket.
A host deadline bounds `docker start -a`; `finally` forcibly removes the named
container and queries Docker to confirm its absence. Cleanup failure is an error.
Docker CLI calls also have deadlines and a 2 MiB capture limit (polled every 50 ms;
this is not an instantaneous disk quota). Do not use this harness for arbitrary
adversarial submissions; Docker isolation and in-process pytest are not containment
or tamper-proof guarantees.

The container entry point emits a JSON report after pytest finishes, before tmpfs is
lost. The host validates its structure and saves raw stdout/stderr, report JSON,
command logs, and environment metadata including image ID/digests, exit code,
cleanup result, and candidate hash. The report records Python/pytest versions and
hashes of baked-in Python tests. All report contents can potentially be influenced
by candidate execution; retain raw evidence and review observed violations.

A finished assertion-failure run is `completed`, not an infrastructure error.
Timeouts, unavailable Docker/image, missing/malformed/contradictory reports, empty
runs, collection errors, and setup/teardown errors are `error`. Skips remain skips.
The record's `findings` list stays empty; the D decision is derived from the failed
security tests. Passing checks is not proof of security: the payload lists are fixed and finite. Tests cover the three adapted contracts, not the entire original
SecurityEval benchmark. Command timeout internals and concurrent filesystem races
are not established by these behavioral tests. No fuzzing or repair is implemented.

The base tag is a development convenience. For published experiments pin `FROM`
to a reviewed digest, pin test dependencies, retain the built image, and archive
its identity plus all test/configuration/source files with the evidence.
