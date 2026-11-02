"""Synthetic Claude fixtures validate the harness, never model performance."""

import json
from pathlib import Path
from types import SimpleNamespace

import httpx2
import pytest
from anthropic import Anthropic

from security_eval.cli import main
from security_eval.contracts import load_samples, validate
from security_eval.generation import (
    candidate_id,
    estimate_cost_usd,
    extract_code,
    generate,
    prepare,
    run_batch,
    run_experiment,
)


@pytest.fixture
def sample():
    return load_samples(Path(__file__).resolve().parents[2] / "data/samples.jsonl")[0]


class FixtureResponse:
    def __init__(self, text, *, stop_reason="end_turn", model="fixture-only", usage=None,
                 extra_content=None):
        self.raw = {
            "id": "msg_unit_test_fixture",
            "type": "message",
            "role": "assistant",
            "model": model,
            "content": (extra_content or []) + [{"type": "text", "text": text}],
            "stop_reason": stop_reason,
            "stop_sequence": None,
            "usage": usage or {
                "input_tokens": 10,
                "output_tokens": 20,
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 0,
            },
        }

    def model_dump(self, **kwargs):
        return self.raw


def fixture_client(text, **kwargs):
    response = FixtureResponse(text, **kwargs)
    return SimpleNamespace(messages=SimpleNamespace(create=lambda **request: response))


def test_dry_run_prepares_exact_claude_request(tmp_path, sample):
    out = tmp_path / "prepared"
    record = prepare(sample, out, "claude-haiku-5-5")
    request = json.loads((out / "request.json").read_text())
    assert record["status"] == "prepared"
    assert record["provider"] == "anthropic"
    assert record["candidate_id"] == "sql_delete_user__anthropic__claude-haiku-5-5__run_01"
    assert request == {
        "model": "claude-haiku-5-5",
        "max_tokens": 16000,
        "system": request["system"],
        "messages": [{"role": "user", "content": sample["adapted_prompt"]}],
        "thinking": {"type": "adaptive"},
        "output_config": {"effort": "medium"},
    }
    assert not (out / "code.py").exists()
    with pytest.raises(FileExistsError):
        prepare(sample, out, "claude-haiku-5-5")


@pytest.mark.parametrize("text,expected", [
    ("def f():\n    pass", "def f():\n    pass\n"),
    ("```python\ndef f():\n    pass\n```", "def f():\n    pass\n"),
])
def test_code_extraction(text, expected):
    assert extract_code(text) == expected


def test_generation_saves_but_never_executes_code(tmp_path, sample):
    marker = tmp_path / "must-not-exist"
    code = f"from pathlib import Path\nPath({str(marker)!r}).touch()\ndef remove_user(conn, username):\n    return 0\n"
    out = tmp_path / "fixture"
    record = generate(sample, out, "claude-haiku-5-5", client=fixture_client(code))
    assert record["status"] == "generated"
    assert record["stop_reason"] == "end_turn"
    assert not marker.exists()
    assert (out / "code.py").read_text() == code
    validate("generation", record)


def test_thinking_blocks_are_not_written_as_code(tmp_path, sample):
    code = "def remove_user(conn, username):\n    return 0\n"
    thinking = [{"type": "thinking", "thinking": "Private fixture reasoning", "signature": "x"}]
    out = tmp_path / "fixture"
    record = generate(sample, out, "claude-haiku-5-5",
                      client=fixture_client(code, extra_content=thinking))
    assert record["status"] == "generated"
    assert (out / "completion.txt").read_text() == code
    assert "Private fixture reasoning" in (out / "response.json").read_text()


@pytest.mark.parametrize("text,stop_reason,kind", [
    ("", "end_turn", "empty_response"),
    ("def broken(:", "end_turn", "parsing_error"),
    ("pass", "end_turn", "missing_entry_point"),
    ("def remove_user(): pass", "max_tokens", "truncated"),
    ("", "refusal", "refusal"),
    ("def remove_user(): pass", "tool_use", "unexpected_stop_reason"),
])
def test_bad_or_incomplete_output_is_classified(tmp_path, sample, text, stop_reason, kind):
    record = generate(sample, tmp_path / kind, "claude-haiku-5-5",
                      client=fixture_client(text, stop_reason=stop_reason))
    assert record["status"] == "error"
    assert record["failure_kind"] == kind


def test_api_error_does_not_persist_sensitive_exception_text(tmp_path, sample):
    def fail(**kwargs):
        raise RuntimeError("secret-key-must-not-leak")
    out = tmp_path / "fixture"
    client = SimpleNamespace(messages=SimpleNamespace(create=fail))
    record = generate(sample, out, "claude-haiku-5-5", client=client)
    assert record["status"] == "error"
    assert "secret-key" not in (out / "generation.json").read_text()


def test_missing_key_fails_without_artifacts(tmp_path, sample, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        generate(sample, tmp_path / "missing", "claude-haiku-5-5")
    assert not (tmp_path / "missing").exists()


def test_request_payload_reaches_client_unchanged(tmp_path, sample):
    captured = {}
    code = "def remove_user(conn, username):\n    return 0\n"
    def create(**request):
        captured.update(request)
        return FixtureResponse(code, model=request["model"])
    client = SimpleNamespace(messages=SimpleNamespace(create=create))
    record = generate(sample, tmp_path / "fixture", "claude-haiku-5-5", client=client,
                      effort="medium", max_tokens=16000)
    assert record["status"] == "generated"
    assert captured["thinking"] == {"type": "adaptive"}
    assert captured["output_config"] == {"effort": "medium"}
    assert captured["max_tokens"] == 16000
    assert captured["messages"] == [{"role": "user", "content": sample["adapted_prompt"]}]


def test_anthropic_sdk_serializes_fixed_request(tmp_path, sample):
    def handler(request):
        payload = json.loads(request.content)
        assert request.url.path == "/v1/messages"
        assert payload["thinking"] == {"type": "adaptive"}
        assert payload["output_config"] == {"effort": "medium"}
        assert payload["max_tokens"] == 16000
        assert payload["messages"] == [{"role": "user", "content": sample["adapted_prompt"]}]
        return httpx2.Response(200, json={
            "id": "msg_sdk_fixture", "type": "message", "role": "assistant",
            "model": "claude-haiku-5-5",
            "content": [{"type": "text", "text":
                         "def remove_user(conn, username):\n    return 0\n"}],
            "stop_reason": "end_turn", "stop_sequence": None,
            "usage": {"input_tokens": 10, "output_tokens": 20,
                      "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0},
        })
    with httpx2.Client(transport=httpx2.MockTransport(handler)) as http_client:
        with Anthropic(api_key="unit-test-placeholder", base_url="https://api.anthropic.com",
                       http_client=http_client, max_retries=0) as client:
            record = generate(sample, tmp_path / "fixture", "claude-haiku-5-5", client=client)
    assert record["status"] == "generated"
    assert record["response_id"] == "msg_sdk_fixture"


def test_batch_generation_records_one_candidate_per_sample(tmp_path):
    samples = load_samples(Path(__file__).resolve().parents[2] / "data/samples.jsonl")
    code_by_entry = {
        "remove_user": "def remove_user(conn, username):\n    return 0\n",
        "execute_command": "def execute_command(command):\n    return ''\n",
        "read_file": "def read_file(base_dir, filename):\n    return b''\n",
    }
    def create(**request):
        prompt = request["messages"][0]["content"]
        code = next(code for entry, code in code_by_entry.items() if entry in prompt)
        return FixtureResponse(code, model=request["model"])
    client = SimpleNamespace(messages=SimpleNamespace(create=create))
    out = tmp_path / "batch"
    manifest = run_batch(samples, out, "claude-haiku-5-5", client=client)
    assert manifest["status"] == "complete"
    assert all(item["status"] == "generated" and item["code"] for item in manifest["results"])


def test_candidate_ids_and_cost_estimates_are_reproducible():
    assert candidate_id("sql_delete_user", "claude-sonnet-5-5", 3) == (
        "sql_delete_user__anthropic__claude-sonnet-5-5__run_03"
    )
    usage = {"input_tokens": 1000, "output_tokens": 2000,
             "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}
    assert estimate_cost_usd(usage, "claude-haiku-5-5") == 0.0011
    assert estimate_cost_usd(usage, "claude-sonnet-5-5") == 0.022
    assert estimate_cost_usd(usage, "unknown-model") is None


def test_experiment_dry_run_prepares_every_model_sample_and_run(tmp_path):
    samples = load_samples(Path(__file__).resolve().parents[2] / "data/samples.jsonl")
    out = tmp_path / "experiment"
    manifest = run_experiment(
        samples, out, ["claude-haiku-5-5", "claude-sonnet-5-5"], runs=2,
        dry_run=True, effort="medium", max_tokens=16000,
    )
    assert manifest["status"] == "complete"
    assert manifest["provider"] == "anthropic"
    assert manifest["expected_candidates"] == 12
    assert manifest["status_counts"] == {"prepared": 12, "generated": 0, "error": 0}
    assert len({item["candidate_id"] for item in manifest["results"]}) == 12
    assert not list(out.rglob("code.py"))


def test_experiment_generation_records_cost_and_hashes(tmp_path):
    samples = load_samples(Path(__file__).resolve().parents[2] / "data/samples.jsonl")[:1]
    usage = {"input_tokens": 1000, "output_tokens": 2000,
             "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}
    code = "def remove_user(conn, username):\n    return 0\n"
    client = SimpleNamespace(messages=SimpleNamespace(
        create=lambda **kwargs: FixtureResponse(code, model=kwargs["model"], usage=usage)))
    manifest = run_experiment(
        samples, tmp_path / "experiment", ["claude-haiku-5-5", "claude-sonnet-5-5"],
        runs=1, client=client, effort="medium", max_tokens=16000,
    )
    assert manifest["status"] == "complete"
    assert manifest["estimated_cost_usd"] == 0.0231
    assert all(item["response_sha256"] and item["code_sha256"] for item in manifest["results"])


def test_cli_dry_runs(tmp_path, sample):
    samples = tmp_path / "samples.jsonl"
    samples.write_text(json.dumps(sample) + "\n")
    single = tmp_path / "single"
    assert main(["generate", sample["sample_id"], "--samples", str(samples),
                 "--model", "claude-haiku-5-5", "--out", str(single), "--dry-run"]) == 0
    assert main(["validate", "generation", str(single / "generation.json")]) == 0
    experiment = tmp_path / "experiment"
    assert main(["generate-experiment", "--samples", str(samples), "--models",
                 "claude-haiku-5-5", "claude-sonnet-5-5", "--runs", "2",
                 "--out", str(experiment), "--dry-run"]) == 0
    manifest = json.loads((experiment / "manifest.json").read_text())
    assert manifest["expected_candidates"] == 4
    assert manifest["parameters"] == {"max_tokens": 16000, "effort": "medium"}
