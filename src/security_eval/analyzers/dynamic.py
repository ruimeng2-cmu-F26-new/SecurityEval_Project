"""Host-side bounded Docker execution. Never import candidates on the host."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import uuid

from jsonschema import ValidationError

from .base import pending
from ..contracts import utc_now, validate, write_json
from ..generation import digest

SAMPLES = {
    "sql_delete_user", "command_allowlist", "path_read_file", "sql_list_users", "command_count_lines",
    "path_extract_tar", "eval_expression", "url_host_allowlist", "redirect_next_url", "log_login_attempt",
    "html_render_greeting", "random_session_id", "hash_password", "file_create_executable", "html_filter_script",
    # tasks first tried as pilot probes
    "http_response_header", "html_profile_link", "regex_find_word", "error_computation_response",
    "tls_client_context", "cookie_session", "xml_parse_note", "upload_save_pdf", "log_conversion_error",
    "url_github_user", "temp_write_results",
}
PREFIX = "SECURITY_EVAL_REPORT="
MAX_OUTPUT = 2 * 1024 * 1024


class RunnerError(RuntimeError):
    def __init__(self, message, stdout="", stderr=""):
        super().__init__(message)
        self.stdout = stdout
        self.stderr = stderr


def command(args, timeout=15):
    """Bound CLI lifetime and captured output without an unbounded PIPE buffer."""
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        with subprocess.Popen(args, stdout=stdout, stderr=stderr) as process:
            deadline = time.monotonic() + timeout
            failure = None
            while process.poll() is None:
                if stdout.tell() + stderr.tell() > MAX_OUTPUT:
                    failure = "OutputLimit: Docker output exceeded 2 MiB"
                    break
                if time.monotonic() >= deadline:
                    failure = "Timeout: Docker command deadline exceeded"
                    break
                time.sleep(0.05)
            if failure:
                process.kill()
                process.wait()
            if os.fstat(stdout.fileno()).st_size + os.fstat(stderr.fileno()).st_size > MAX_OUTPUT:
                failure = "OutputLimit: Docker output exceeded 2 MiB"
            stdout.seek(0)
            stderr.seek(0)
            out = stdout.read(MAX_OUTPUT).decode("utf-8", errors="replace")
            err = stderr.read(MAX_OUTPUT).decode("utf-8", errors="replace")
            if failure:
                raise RunnerError(failure, out, err)
            if len(out.encode()) + len(err.encode()) > MAX_OUTPUT:
                raise RunnerError("OutputLimit: Docker output exceeded 2 MiB")
            return process.returncode, out, err


def parse_report(stdout, exit_code, sample_id):
    reports = [line[len(PREFIX):] for line in stdout.splitlines() if line.startswith(PREFIX)]
    if len(reports) != 1:
        raise RunnerError("ReportError: expected exactly one container report")
    report = json.loads(reports[0])
    if report["sample_id"] != sample_id or report["exit_code"] != exit_code:
        raise RunnerError("ReportError: sample or exit code mismatch")
    if exit_code not in (0, 1) or report["collection_errors"] or not report["tests"]:
        raise RunnerError("ExecutionError: collection, execution, or empty test run")
    if any(test["outcome"] == "error" for test in report["tests"]):
        raise RunnerError("ExecutionError: test setup or teardown failed")
    if exit_code == 0 and any(t["outcome"] == "failed" for t in report["tests"]):
        raise RunnerError("ReportError: contradictory test results")
    if exit_code == 1 and not any(t["outcome"] == "failed" for t in report["tests"]):
        raise RunnerError("ReportError: failure exit without failed tests")
    return report


class DockerPytestAnalyzer:
    def __init__(self, evidence_dir=None, image="security-eval-tests:dev", timeout=30):
        self.evidence_dir = Path(evidence_dir) if evidence_dir is not None else None
        self.image = image
        self.timeout = timeout

    def analyze(self, code_path: Path, sample: dict, run_id: str) -> dict:
        record = pending(code_path, sample, run_id, "pytest-docker")
        if self.evidence_dir is None:
            record["notes"] = "Execution not configured: supply evidence_dir to enable Docker."
            return record
        directory = self.evidence_dir
        directory.mkdir(parents=True, exist_ok=False)
        record.update(status="error", started_at=utc_now())
        name = "security-eval-" + uuid.uuid4().hex
        metadata = {"container_name": name, "requested_image": self.image,
                    "timeout_seconds": self.timeout, "code_sha256": record["code_sha256"],
                    "commands": [], "cleanup_confirmed": False}
        logs = []

        def invoke(args, timeout=15):
            metadata["commands"].append(args)
            try:
                result = command(args, timeout)
            except RunnerError as exc:
                logs.append({"command": args, "error": str(exc)})
                (directory / "stdout.txt").write_text(exc.stdout, encoding="utf-8")
                (directory / "stderr.txt").write_text(exc.stderr, encoding="utf-8")
                raise
            logs.append({"command": args, "exit_code": result[0],
                         "stdout": result[1], "stderr": result[2]})
            return result

        attempted_create = False
        try:
            if sample["sample_id"] not in SAMPLES:
                raise RunnerError("UnsupportedSample: no candidate tests available")
            rc, stdout, stderr = invoke(["docker", "image", "inspect", self.image])
            if rc:
                raise RunnerError("ImageUnavailable: " + stderr[:2000])
            image = json.loads(stdout)[0]
            metadata["image_id"] = image["Id"]
            metadata["repo_digests"] = image.get("RepoDigests", [])
            # Snapshot exact bytes: candidate and hash cannot diverge if source changes later.
            with tempfile.TemporaryDirectory(prefix="security-eval-") as staging:
                candidate = Path(staging) / "code.py"
                candidate.write_bytes(code_path.read_bytes())
                candidate.chmod(0o444)
                Path(staging).chmod(0o755)
                if digest(candidate.read_bytes()) != record["code_sha256"]:
                    raise RunnerError("CandidateChanged: source hash changed before execution")
                args = ["docker", "create", "--name", name, "--pull", "never",
                        "--network", "none", "--read-only", "--user", "10001:10001",
                        "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
                        "--pids-limit", "64", "--memory", "256m", "--memory-swap", "256m",
                        "--cpus", "1", "--ulimit", "nofile=256:256",
                        "--log-opt", "max-size=1m", "--log-opt", "max-file=1",
                        "--tmpfs", "/tmp:rw,nosuid,nodev,size=64m,mode=1777",
                        "--mount", f"type=bind,source={candidate},target=/candidate/code.py,readonly",
                        "--entrypoint", "python", image["Id"], "/opt/run_tests.py", sample["sample_id"]]
                attempted_create = True
                rc, _, stderr = invoke(args)
                if rc:
                    raise RunnerError("CreateError: " + stderr[:2000])
                rc, stdout, stderr = invoke(["docker", "start", "-a", name], self.timeout)
                (directory / "stdout.txt").write_text(stdout, encoding="utf-8")
                (directory / "stderr.txt").write_text(stderr, encoding="utf-8")
                metadata["exit_code"] = rc
                # Save raw structured report even when execution was unsuccessful.
                lines = [s[len(PREFIX):] for s in stdout.splitlines() if s.startswith(PREFIX)]
                if len(lines) == 1:
                    write_json(directory / "report.json", json.loads(lines[0]))
                report = parse_report(stdout, rc, sample["sample_id"])
                completed = {**record, "status": "completed", "tests": report["tests"],
                             "tool_version": "pytest " + report["pytest_version"], "error": None,
                             "completed_at": utc_now(), "evidence_files": ["report.json"]}
                validate("analysis", completed)
                record.update(completed)
        except (OSError, ValueError, KeyError, TypeError, ValidationError, RunnerError) as exc:
            record.update(status="error", error={"type": type(exc).__name__, "message": str(exc)[:4000]})
        finally:
            if attempted_create:
                try:
                    rc, _, stderr = invoke(["docker", "rm", "-f", name])
                    if rc and "No such container" not in stderr:
                        raise RunnerError("CleanupError: " + stderr[:2000])
                    rc, stdout, _ = invoke(["docker", "container", "ls", "-aq", "--filter", f"name=^/{name}$"])
                    if rc or stdout.strip():
                        raise RunnerError("CleanupError: container removal not confirmed")
                    metadata["cleanup_confirmed"] = True
                except (OSError, RunnerError) as exc:
                    record.update(status="error", error={"type": "CleanupError", "message": str(exc)[:4000]})
            write_json(directory / "environment.json", metadata)
            write_json(directory / "commands.json", {"commands": logs})
        record["completed_at"] = utc_now()
        record["evidence_files"] = [f"{directory.name}/{p.name}" for p in sorted(directory.iterdir())]
        record["notes"] = (
            "Container reports are not tamper-proof. Failed tests are not automatically vulnerabilities; "
            "passing tests establish only the checked behavior. No automatic findings or repair."
        )
        validate("analysis", record)
        return record
