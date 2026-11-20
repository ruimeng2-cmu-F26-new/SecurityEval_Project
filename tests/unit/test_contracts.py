import copy
import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import ValidationError

from security_eval.contracts import load_samples, validate
from security_eval.analyzers.dynamic import DockerPytestAnalyzer

# Formal experiment tasks, and tasks kept only for harness tests and controls (first: sql_delete_user).
FORMAL = Path(__file__).resolve().parents[2] / "data/samples.jsonl"
SAMPLES = Path(__file__).resolve().parents[2] / "data/extra_samples.jsonl"


def test_selected_samples_have_stable_original_prompt_hashes():
    samples = load_samples(FORMAL) + load_samples(SAMPLES)
    assert len(load_samples(FORMAL)) == 15 and len(samples) == 26
    assert len({s["sample_id"] for s in samples}) == 26
    for sample in samples:
        assert hashlib.sha256(sample["original_prompt"].encode()).hexdigest() == sample["source"]["prompt_sha256"]
        assert sample["original_prompt"] != sample["adapted_prompt"]


def test_generation_prompts_are_frozen_function_only_variants():
    expected = {
        "log_login_attempt": "d558d2dc53be8b9c588d49f778002ae7716e9d7e8103050ebdd6d21f06562f73",
        "error_computation_response": "6c1d076e35f5c918622518da5abfb07eec2cd24a652294f8bfd1f3a48c42b529",
        "xml_parse_note": "280221e624d094ecd6d8bbf1a8c68264ad9ad3aaad30dd8b393c4afbe1b42ee1",
        "html_profile_link": "ddcfd85aca8c2a18acc8d91ad9a845fad559bb1005add95b1818e8ee8dcf44da",
        "html_filter_script": "e0a1a1f0c4ef7ddebc36baf0ae9ae9f3de44bd2a47586d8df6cfbbb2d5e3fc46",
        "path_extract_tar": "a32d5276d8ab882b7e073880a2d764e960cc2d3e64dee24aa83f729f048064d7",
        "sql_list_users": "c720282881bdf9bfb5e9770b8e17ca82c9d18f18130c789f50628c3f34168ebf",
        "redirect_next_url": "712595e7bdd63b1d49be57cedf939dd6d78762959fc9907ddf2c61eab8de1ef7",
        "random_session_id": "2c22f60aea1f0b3127d173b7f6ef8f1c6916011dbbfc30b5408f891e1cc2180d",
        "eval_expression": "8b189caa4954acf20f82114ff38f77eebb11c775256e1ad8976180fb6ecbf72a",
        "hash_password": "5d657cc557ba140958e1581977a71e0108466e8d6283458bc9c8d516cafb2dbd",
        "file_create_executable": "39ff445e199ed89c3ec71192a5ae60e2b83a681277ac99f2208261389103e807",
        "html_render_greeting": "4fc94a08535f4b738007a4fac73f908cdbeb18cbe7d34f3fbe04c4e9dfd321b0",
        "url_host_allowlist": "f0ab81bc55268de920a419cc21f974dfbe71394108342c104eb1ba67e9423947",
        "command_count_lines": "6f0dd16633e3f62d0bb1d681a2ee6b589cd861725f78974309430128aa3c7ff9",
    }
    samples = load_samples(FORMAL)
    assert {sample["sample_id"] for sample in samples} == set(expected)
    for sample in samples:
        actual = hashlib.sha256(sample["adapted_prompt"].encode()).hexdigest()
        assert actual == expected[sample["sample_id"]]


@pytest.mark.parametrize("mutation", ["missing", "unknown", "invalid_id"])
def test_invalid_sample_contracts_are_rejected(mutation):
    sample = copy.deepcopy(load_samples(SAMPLES)[0])
    if mutation == "missing":
        del sample["original_prompt"]
    elif mutation == "unknown":
        sample["made_up_result"] = "passed"
    else:
        sample["sample_id"] = "../../escape"
    with pytest.raises(ValidationError):
        validate("sample", sample)


def test_duplicate_samples_are_rejected(tmp_path):
    sample = load_samples(SAMPLES)[0]
    path = tmp_path / "duplicate.jsonl"
    path.write_text((json.dumps(sample) + "\n") * 2)
    with pytest.raises(ValueError, match="Duplicate"):
        load_samples(path)


@pytest.mark.parametrize("analyzer", [DockerPytestAnalyzer()])
def test_unimplemented_analyzers_cannot_claim_success(analyzer, tmp_path):
    code = tmp_path / "fixture.py"
    code.write_text("raise RuntimeError('must never execute')\n")
    record = analyzer.analyze(code, load_samples(SAMPLES)[0], "unit-test-only")
    assert record["status"] == "not_run"
    assert record["findings"] == record["tests"] == []
    assert record["code_sha256"] == hashlib.sha256(code.read_bytes()).hexdigest()
    record["status"] = "completed"
    with pytest.raises(ValidationError):
        validate("analysis", record)


def test_not_run_cannot_contain_test_results(tmp_path):
    code = tmp_path / "fixture.py"
    code.write_text("pass\n")
    record = DockerPytestAnalyzer().analyze(code, load_samples(SAMPLES)[0], "unit-test-only")
    record["tests"] = [{"test_id": "fake", "category": "security", "outcome": "passed", "message": ""}]
    with pytest.raises(ValidationError):
        validate("analysis", record)
