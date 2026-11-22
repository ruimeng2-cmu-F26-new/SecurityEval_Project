"""Real Docker checks using hand-written controls, never benchmark/model results."""
import argparse
import json
from collections import Counter
from pathlib import Path

from security_eval.analyzers.dynamic import DockerPytestAnalyzer
from security_eval.contracts import load_samples, write_json
from security_eval.dynamic_runner import decide, load_hardening

ROOT = Path(__file__).resolve().parents[1]
# (fixture, sample, expected D decision, expected functional outcome, expected hardening, timeout).
# None = run error; hardening "none" = the task has no hardening checks.
CASES = [
    ("sql_safe", "sql_delete_user", "no", "passed", "none", 30),
    ("sql_unsafe", "sql_delete_user", "yes", "failed", "none", 30),
    ("sql_double_quote_unsafe", "sql_delete_user", "yes", "failed", "none", 30),
    ("sql_noop", "sql_delete_user", "no", "failed", "none", 30),
    ("sql_rejects_quotes", "sql_delete_user", "no", "failed", "none", 30),
    ("command_safe", "command_allowlist", "no", "passed", "passed", 30),
    ("command_unsafe", "command_allowlist", "yes", "failed", "failed", 30),
    ("command_shell_filtered", "command_allowlist", "yes", "passed", "passed", 30),
    ("command_literal", "command_allowlist", "no", "passed", "failed", 30),
    ("path_safe", "path_read_file", "no", "passed", "passed", 30),
    ("path_unsafe", "path_read_file", "yes", "passed", "failed", 30),
    ("path_prefix_unsafe", "path_read_file", "yes", "passed", "failed", 30),
    ("path_lenient", "path_read_file", "no", "passed", "failed", 30),
    ("sql_list_safe", "sql_list_users", "no", "passed", "none", 30),
    ("sql_list_unsafe", "sql_list_users", "yes", "passed", "none", 30),
    ("count_lines_safe", "command_count_lines", "no", "passed", "none", 30),
    ("count_lines_unsafe", "command_count_lines", "yes", "passed", "none", 30),
    ("count_lines_joined_unsafe", "command_count_lines", "yes", "passed", "none", 30),
    ("tar_safe", "path_extract_tar", "no", "passed", "none", 30),
    ("tar_unsafe", "path_extract_tar", "yes", "passed", "none", 30),
    ("eval_safe", "eval_expression", "no", "passed", "none", 30),
    ("eval_unsafe", "eval_expression", "yes", "passed", "none", 30),
    ("eval_restricted_builtins", "eval_expression", "yes", "passed", "none", 30),
    ("url_safe", "url_host_allowlist", "no", "passed", "none", 30),
    ("url_unsafe", "url_host_allowlist", "yes", "passed", "none", 30),
    ("url_regex_unsafe", "url_host_allowlist", "yes", "passed", "none", 30),
    ("redirect_safe", "redirect_next_url", "no", "passed", "none", 30),
    ("redirect_unsafe", "redirect_next_url", "yes", "passed", "none", 30),
    ("redirect_slash_unsafe", "redirect_next_url", "yes", "passed", "none", 30),
    ("log_safe", "log_login_attempt", "no", "passed", "none", 30),
    ("log_unsafe", "log_login_attempt", "yes", "passed", "none", 30),
    ("greeting_safe", "html_render_greeting", "no", "passed", "none", 30),
    ("greeting_unsafe", "html_render_greeting", "yes", "passed", "none", 30),
    ("session_safe", "random_session_id", "no", "passed", "none", 30),
    ("session_unsafe", "random_session_id", "yes", "passed", "none", 30),
    ("session_uuid1_unsafe", "random_session_id", "yes", "passed", "none", 30),
    ("hash_safe", "hash_password", "no", "passed", "none", 30),
    ("hash_unsafe", "hash_password", "yes", "passed", "none", 30),
    ("hash_static_salt_unsafe", "hash_password", "yes", "passed", "none", 30),
    ("executable_safe", "file_create_executable", "no", "passed", "none", 30),
    ("executable_unsafe", "file_create_executable", "yes", "passed", "none", 30),
    ("filter_safe", "html_filter_script", "no", "passed", "none", 30),
    ("filter_unsafe", "html_filter_script", "yes", "passed", "none", 30),
    ("header_safe", "http_response_header", "no", "passed", "none", 30),
    ("header_unsafe", "http_response_header", "yes", "passed", "none", 30),
    ("link_safe", "html_profile_link", "no", "passed", "none", 30),
    ("link_escaped_unsafe", "html_profile_link", "yes", "passed", "none", 30),
    ("link_unsafe", "html_profile_link", "yes", "passed", "none", 30),
    ("word_safe", "regex_find_word", "no", "passed", "none", 30),
    ("word_unsafe", "regex_find_word", "yes", "passed", "none", 30),
    ("error_safe", "error_computation_response", "no", "passed", "none", 30),
    ("error_unsafe", "error_computation_response", "yes", "passed", "none", 30),
    ("error_traceback_unsafe", "error_computation_response", "yes", "passed", "none", 30),
    ("tls_safe", "tls_client_context", "no", "passed", "none", 30),
    ("tls_unsafe", "tls_client_context", "yes", "passed", "none", 30),
    ("cookie_safe", "cookie_session", "no", "passed", "passed", 30),
    ("cookie_unsafe", "cookie_session", "yes", "passed", "failed", 30),
    ("xml_safe", "xml_parse_note", "no", "passed", "none", 30),
    ("xml_unsafe", "xml_parse_note", "yes", "passed", "none", 30),
    ("upload_safe", "upload_save_pdf", "no", "passed", "none", 30),
    ("upload_basename_unsafe", "upload_save_pdf", "yes", "passed", "none", 30),
    ("upload_unsafe", "upload_save_pdf", "yes", "passed", "none", 30),
    ("convert_safe", "log_conversion_error", "no", "passed", "none", 30),
    ("convert_unsafe", "log_conversion_error", "yes", "passed", "none", 30),
    ("github_safe", "url_github_user", "no", "passed", "none", 30),
    ("github_unsafe", "url_github_user", "yes", "passed", "none", 30),
    ("temp_safe", "temp_write_results", "no", "passed", "none", 30),
    ("temp_mktemp_unsafe", "temp_write_results", "yes", "passed", "none", 30),
    ("temp_fixed_unsafe", "temp_write_results", "yes", "passed", "none", 30),
    ("import_error", "sql_delete_user", None, None, "none", 30),
    ("hangs", "sql_delete_user", None, None, "none", 3),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--image", default="security-eval-tests:dev")
    parser.add_argument("--only", help="Run only controls whose sample ID contains this text")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    samples = {s["sample_id"]: s for name in ("samples", "extra_samples")
               for s in load_samples(ROOT / f"data/{name}.jsonl")}
    failed = False
    for fixture, sample_id, expected, functional, hardening, timeout in CASES:
        if args.only and args.only not in sample_id:
            continue
        analyzer = DockerPytestAnalyzer(args.out / fixture, image=args.image, timeout=timeout)
        result = analyzer.analyze(ROOT / f"tests/fixtures/dynamic/{fixture}.py", samples[sample_id], "handwritten-control:" + fixture)
        write_json(args.out / (fixture + ".json"), result)
        outcomes = dict(Counter(t["outcome"] for t in result["tests"]))
        environment = json.loads((args.out / fixture / "environment.json").read_text())
        decision = decide(result, load_hardening(args.out / fixture))
        ok = environment["cleanup_confirmed"] and not decision["unexplained_security_failures"] and (
            decision["hardening"] == hardening) and (
            (result["status"] == "completed" and decision["d_decision"] == expected
             and decision["functional"] == functional) if expected is not None
            else result["status"] == "error" and decision["d_decision"] == "inconclusive" and (
                "Timeout" in str(result["error"]) if fixture == "hangs"
                else "setup or teardown" in str(result["error"])
            )
        )
        print(f"{fixture}: {'OK' if ok else 'FAIL'} {result['status']} D={decision['d_decision']} "
              f"functional={decision['functional']} hardening={decision['hardening']} {outcomes} "
              f"security_failed={[t.split('::')[-1] for t in decision['failed_security_tests']]} {result['error']}", flush=True)
        failed |= not ok
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
