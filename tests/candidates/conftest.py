"""Load candidates only inside the Docker test environment."""

import importlib.util
from pathlib import Path

import pytest


@pytest.fixture
def candidate_module():
    # Docker runner will mount the candidate at this fixed path.
    # Keep loading inside the fixture, not at module import time.
    candidate_path = Path("/candidate/code.py")
    if not candidate_path.is_file():
        pytest.fail("Candidate missing: run these tests through Docker")

    spec = importlib.util.spec_from_file_location(
        "candidate_under_test", candidate_path
    )
    if spec is None or spec.loader is None:
        pytest.fail("Could not load candidate")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


@pytest.fixture
def remove_user(candidate_module):
    entry_point = getattr(candidate_module, "remove_user", None)
    if not callable(entry_point):
        pytest.fail("Candidate must define callable remove_user")

    return entry_point

@pytest.fixture
def execute_command(candidate_module):
    return candidate_module.execute_command


@pytest.fixture
def read_file(candidate_module):
    return candidate_module.read_file


def _entry_point_fixture(name):
    @pytest.fixture(name=name)
    def entry_point(candidate_module):
        function = getattr(candidate_module, name, None)
        if not callable(function):
            pytest.fail(f"Candidate must define callable {name}")
        return function
    return entry_point


for _name in ("list_users", "count_lines", "extract_tar", "evaluate_expression", "is_allowed_url",
              "get_redirect_target", "log_login_attempt", "render_greeting", "generate_session_id",
              "hash_password", "create_executable_file", "filter_script_tags",
              # tasks first tried as pilot probes
              "build_response_head", "render_profile_link", "find_lines_with_word", "run_computation",
              "get_ssl_context", "build_session_cookie", "parse_note", "save_pdf_upload", "convert_to_int",
              "build_user_api_url", "write_results"):
    globals()["_entry_point_" + _name] = _entry_point_fixture(_name)
