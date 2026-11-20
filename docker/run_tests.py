"""Container-only pytest entry point. Reports are observations, not tamper-proof attestations."""
import hashlib
import json
from pathlib import Path
import platform
import sys

import pytest

SAMPLES = [
    "sql_delete_user", "command_allowlist", "path_read_file", "sql_list_users", "command_count_lines",
    "path_extract_tar", "eval_expression", "url_host_allowlist", "redirect_next_url", "log_login_attempt",
    "html_render_greeting", "random_session_id", "hash_password", "file_create_executable", "html_filter_script",
    # tasks first tried as pilot probes
    "http_response_header", "html_profile_link", "regex_find_word", "error_computation_response",
    "tls_client_context", "cookie_session", "xml_parse_note", "upload_save_pdf", "log_conversion_error",
    "url_github_user", "temp_write_results",
]
FILES = {sample: f"test_{sample}.py" for sample in SAMPLES}
PREFIX = "SECURITY_EVAL_REPORT="


class Recorder:
    def __init__(self):
        self.categories = {}
        self.results = {}
        self.collection_errors = []

    def pytest_collection_modifyitems(self, items):
        for item in items:
            categories = [m for m in ("functional", "security", "hardening") if item.get_closest_marker(m)]
            if len(categories) != 1:
                raise pytest.UsageError("Each candidate test needs exactly one category")
            self.categories[item.nodeid] = categories[0]

    def pytest_collectreport(self, report):
        if report.failed:
            self.collection_errors.append(str(report.longrepr)[:12000])

    def pytest_runtest_logreport(self, report):
        if report.when != "call" and report.passed:
            return
        outcome = report.outcome
        if report.failed and report.when != "call":
            outcome = "error"
        old = self.results.get(report.nodeid)
        if old and old["outcome"] == "error":
            return
        self.results[report.nodeid] = {
            "test_id": report.nodeid,
            "category": self.categories[report.nodeid],
            "outcome": outcome,
            "message": str(report.longrepr)[:12000] if report.longrepr else "",
        }


def main():
    sample = sys.argv[1]
    test_file = FILES[sample]
    # Hash before candidate import; persist the exact test environment identity.
    hashes = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in Path("/tests").glob("*.py")
    }
    recorder = Recorder()
    exit_code = int(pytest.main([
        f"/tests/{test_file}", "-v", "--strict-markers", "-p", "no:cacheprovider",
        "--basetemp=/tmp/pytest", "--capture=fd",
    ], plugins=[recorder]))
    # Hardening checks are descriptive: they stay out of the contract's `tests` list and
    # their failures do not make the run fail.
    results = list(recorder.results.values())
    tests = [r for r in results if r["category"] != "hardening"]
    if exit_code == 1 and not any(r["outcome"] in ("failed", "error") for r in tests):
        exit_code = 0
    payload = {
        "sample_id": sample, "exit_code": exit_code,
        "python_version": platform.python_version(), "pytest_version": pytest.__version__,
        "test_sha256": hashes, "tests": tests,
        "hardening_tests": [r for r in results if r["category"] == "hardening"],
        "collection_errors": recorder.collection_errors,
    }
    print("\n" + PREFIX + json.dumps(payload), flush=True)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
