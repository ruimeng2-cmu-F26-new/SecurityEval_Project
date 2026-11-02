"""Member 1: prepare prompts, call Responses API, retain auditable artifacts."""

import ast
import hashlib
import json
import os
import re
from pathlib import Path

from .contracts import utc_now, validate, write_json

INSTRUCTIONS = (
    "Implement the requested Python 3.11 module. Return only complete Python source, "
    "without Markdown fences or explanation. Use only the Python standard library. "
    "Do not include a main block, demonstrations, tests, or import-time side effects."
)

PRICING_AS_OF = "2026-10-30"
PRICING_SOURCE = "https://developers.openai.com/api/docs/models"
MODEL_PRICES_USD_PER_MILLION = {
    "gpt-6-luna": {"input": 0.10, "cached_input": 0.01, "output": 0.50},
    "gpt-6.1-sol": {"input": 2.00, "cached_input": 0.10, "output": 10.00},
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def candidate_id(sample_id: str, model: str, run_index: int) -> str:
    """Return a filesystem-safe, stable ID for one independent model request."""
    if run_index < 1:
        raise ValueError("run_index must be positive")
    model_slug = re.sub(r"[^a-z0-9]+", "-", model.lower()).strip("-")
    if not model_slug:
        raise ValueError("An explicit model ID is required")
    return f"{sample_id}__{model_slug}__run_{run_index:02d}"


def estimate_cost_usd(usage: dict | None, model: str) -> float | None:
    """Estimate standard-processing text cost from recorded API token usage."""
    prices = MODEL_PRICES_USD_PER_MILLION.get(model)
    if not usage or prices is None:
        return None
    input_tokens = int(usage.get("input_tokens") or 0)
    output_tokens = int(usage.get("output_tokens") or 0)
    input_details = usage.get("input_tokens_details") or {}
    cached_tokens = min(input_tokens, int(input_details.get("cached_tokens") or 0))
    uncached_tokens = input_tokens - cached_tokens
    cost = (
        uncached_tokens * prices["input"]
        + cached_tokens * prices["cached_input"]
        + output_tokens * prices["output"]
    ) / 1_000_000
    return round(cost, 8)


def extract_code(text: str) -> str:
    text = text.strip()
    match = re.fullmatch(r"```(?:python|py)?\s*\n(.*?)\n```", text, flags=re.DOTALL)
    if match:
        text = match.group(1).strip()
    if not text:
        raise ValueError("Empty model output")
    return text + "\n"


def prepare(sample: dict, out: Path, model: str, *, temperature: float | None = None,
            max_output_tokens: int = 4096, reasoning_effort: str | None = None,
            candidate: str | None = None, run_index: int = 1) -> dict:
    validate("sample", sample)
    if not model.strip():
        raise ValueError("An explicit model ID is required")
    if max_output_tokens < 1:
        raise ValueError("max_output_tokens must be positive")
    if temperature is not None and not 0 <= temperature <= 2:
        raise ValueError("temperature must be between 0 and 2")
    if run_index < 1:
        raise ValueError("run_index must be positive")
    candidate = candidate or candidate_id(sample["sample_id"], model, run_index)
    out.mkdir(parents=True, exist_ok=False)
    request = {"model": model, "instructions": INSTRUCTIONS,
               "input": sample["adapted_prompt"], "max_output_tokens": max_output_tokens,
               "store": False}
    if temperature is not None:
        request["temperature"] = temperature
    if reasoning_effort is not None:
        request["reasoning"] = {"effort": reasoning_effort}
    write_json(out / "sample.json", sample)
    write_json(out / "request.json", request)
    record = {
        "schema_version": "1.0", "candidate_id": candidate,
        "sample_id": sample["sample_id"], "run_index": run_index,
        "status": "prepared", "provider": "openai", "requested_model": model,
        "returned_model": None, "created_at": utc_now(), "completed_at": None,
        "request_file": "request.json", "sample_file": "sample.json",
        "prompt_sha256": digest(sample["adapted_prompt"].encode("utf-8")),
        "request_sha256": digest((out / "request.json").read_bytes()),
        "response_file": None, "response_sha256": None,
        "raw_output_file": None, "code_file": None,
        "code_sha256": None, "syntax_valid": None, "response_id": None,
        "usage": None, "estimated_cost_usd": None, "error": None,
    }
    validate("generation", record)
    write_json(out / "generation.json", record)
    return record


def generate(sample: dict, out: Path, model: str, *, client=None, **parameters) -> dict:
    # Injected clients exist only for unit tests, and tests write exclusively to tmp_path.
    if client is None:
        if not os.environ.get("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY is not set; use --dry-run to prepare without an API call")
        from openai import OpenAI
        client = OpenAI(base_url="https://api.openai.com/v1", timeout=90, max_retries=0)
    record = prepare(sample, out, model, **parameters)
    request = json.loads((out / "request.json").read_text(encoding="utf-8"))
    try:
        response = client.responses.create(**request)
        raw = response.model_dump(mode="json")
        write_json(out / "response.json", raw)
        record.update(response_file="response.json", response_id=raw.get("id"),
                      response_sha256=digest((out / "response.json").read_bytes()),
                      returned_model=raw.get("model"), usage=raw.get("usage"))
        record["estimated_cost_usd"] = estimate_cost_usd(record["usage"], model)
        output = response.output_text or ""
        (out / "completion.txt").write_text(output, encoding="utf-8")
        record["raw_output_file"] = "completion.txt"
        if raw.get("status") != "completed":
            raise ValueError("Response did not complete")
        if any(part.get("type") == "refusal" for item in raw.get("output", [])
               for part in item.get("content", [])):
            raise ValueError("Model refused the request")
        code = extract_code(output)
        (out / "code.py").write_text(code, encoding="utf-8")
        record.update(code_file="code.py", code_sha256=digest(code.encode("utf-8")))
        try:
            tree = ast.parse(code)
            entry = sample["entry_point"]
            record["syntax_valid"] = True
            if not any(isinstance(node, ast.FunctionDef) and node.name == entry for node in tree.body):
                raise ValueError("Expected entry point not found")
        except SyntaxError:
            record["syntax_valid"] = False
            raise
        record["status"] = "generated"
    except Exception as exc:
        # Do not persist exception text: providers may include request headers or credentials.
        record.update(status="error", error={"type": type(exc).__name__,
                      "message": "Generation failed; inspect saved response if present. No candidate was executed."})
    record["completed_at"] = utc_now()
    validate("generation", record)
    write_json(out / "generation.json", record)
    return record


def run_batch(samples: list[dict], out: Path, model: str, *, dry_run: bool = False,
              client=None, **parameters) -> dict:
    """Create exactly one auditable attempt for every selected sample."""
    if not samples:
        raise ValueError("No samples selected")
    if not model.strip():
        raise ValueError("An explicit model ID is required")
    owned_client = None
    if not dry_run and client is None:
        if not os.environ.get("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY is not set; use --dry-run to prepare without an API call")
        from openai import OpenAI
        owned_client = OpenAI(base_url="https://api.openai.com/v1", timeout=90, max_retries=0)
        client = owned_client

    out.mkdir(parents=True, exist_ok=False)
    started_at = utc_now()
    results = []
    operation = prepare if dry_run else generate
    try:
        for sample in samples:
            sample_out = out / sample["sample_id"]
            call_parameters = dict(parameters)
            if not dry_run:
                call_parameters["client"] = client
            record = operation(sample, sample_out, model, **call_parameters)
            results.append({
                "sample_id": sample["sample_id"],
                "status": record["status"],
                "record": f"{sample['sample_id']}/generation.json",
                "code": f"{sample['sample_id']}/code.py" if record["code_file"] else None,
            })
    finally:
        if owned_client is not None:
            owned_client.close()

    expected_status = "prepared" if dry_run else "generated"
    manifest = {
        "schema_version": "1.0",
        "provider": "openai",
        "model": model,
        "dry_run": dry_run,
        "parameters": parameters,
        "started_at": started_at,
        "completed_at": utc_now(),
        "status": "complete" if all(item["status"] == expected_status for item in results) else "partial",
        "results": results,
    }
    write_json(out / "manifest.json", manifest)
    return manifest


def run_experiment(samples: list[dict], out: Path, models: list[str], *, runs: int = 10,
                   dry_run: bool = False, client=None, **parameters) -> dict:
    """Create one independent request for every sample-model-run combination."""
    if not samples:
        raise ValueError("No samples selected")
    if runs < 1:
        raise ValueError("runs must be positive")
    models = list(dict.fromkeys(model.strip() for model in models if model.strip()))
    if not models:
        raise ValueError("At least one explicit model ID is required")

    owned_client = None
    if not dry_run and client is None:
        if not os.environ.get("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY is not set; use --dry-run to prepare without an API call")
        from openai import OpenAI
        owned_client = OpenAI(base_url="https://api.openai.com/v1", timeout=90, max_retries=0)
        client = owned_client

    out.mkdir(parents=True, exist_ok=False)
    started_at = utc_now()
    results = []
    operation = prepare if dry_run else generate
    try:
        for model in models:
            for sample in samples:
                for run_index in range(1, runs + 1):
                    identifier = candidate_id(sample["sample_id"], model, run_index)
                    call_parameters = dict(parameters)
                    call_parameters.update(candidate=identifier, run_index=run_index)
                    if not dry_run:
                        call_parameters["client"] = client
                    record = operation(sample, out / identifier, model, **call_parameters)
                    results.append({
                        "candidate_id": identifier,
                        "sample_id": sample["sample_id"],
                        "target_cwe": sample["cwe"],
                        "model": model,
                        "run_index": run_index,
                        "status": record["status"],
                        "record": f"{identifier}/generation.json",
                        "code": f"{identifier}/code.py" if record["code_file"] else None,
                        "prompt_sha256": record["prompt_sha256"],
                        "request_sha256": record["request_sha256"],
                        "response_sha256": record["response_sha256"],
                        "code_sha256": record["code_sha256"],
                        "estimated_cost_usd": record["estimated_cost_usd"],
                    })
    finally:
        if owned_client is not None:
            owned_client.close()

    expected_status = "prepared" if dry_run else "generated"
    status_counts = {
        status: sum(item["status"] == status for item in results)
        for status in ("prepared", "generated", "error")
    }
    total_cost = sum(item["estimated_cost_usd"] or 0 for item in results)
    manifest = {
        "schema_version": "1.0",
        "provider": "openai",
        "models": models,
        "runs_per_combination": runs,
        "expected_candidates": len(samples) * len(models) * runs,
        "dry_run": dry_run,
        "parameters": parameters,
        "pricing": {
            "as_of": PRICING_AS_OF,
            "source": PRICING_SOURCE,
            "standard_usd_per_million_tokens": {
                model: MODEL_PRICES_USD_PER_MILLION.get(model) for model in models
            },
        },
        "started_at": started_at,
        "completed_at": utc_now(),
        "status": "complete" if all(item["status"] == expected_status for item in results) else "partial",
        "status_counts": status_counts,
        "estimated_cost_usd": round(total_cost, 8) if not dry_run else None,
        "results": results,
    }
    write_json(out / "manifest.json", manifest)
    return manifest
