"""CWE-078 candidate tests (line counting through wc); run only inside the Docker runner.

`security` tests fail only when an injected command creates a marker file. A candidate
exception or a rejected input is not a detection.
"""
import time

import pytest

IMPACT = "SECURITY IMPACT (CWE-078): "
# {m} is replaced by a marker path that must never be created; {d} by the log directory.
PATTERNS = {
    "semicolon": "*.log; touch {m}",
    "dollar_substitution": "*.log$(touch {m})",
    "backtick_substitution": "*.log`touch {m}`",
    "pipe": "*.log | tee {m}",
    "and_list": "*.log && touch {m}",
    "or_list": "*.none || touch {m}",
    "newline": "*.log\ntouch {m}",
    "quote_break": "*.log'; touch {m}; '",
    "double_quote_break": '*.log"; touch {m}; "',
}
DIRECTORIES = {
    "semicolon": "{d}; touch {m}; ls {d}",
    "dollar_substitution": "{d}$(touch {m})",
    "quote_break": "{d}'; touch {m}; '",
}
FILE_NAMES = {"semicolon": "z.log; touch {m}", "dollar_substitution": "$(touch {m}).log",
              "backtick_substitution": "`touch {m}`.log"}


@pytest.fixture
def logs(tmp_path):
    directory = tmp_path / "logs"
    directory.mkdir()
    (directory / "a.log").write_text("1\n2\n3\n")
    (directory / "b.log").write_text("1\n2\n")
    (directory / "c.txt").write_text("1\n2\n3\n4\n")
    return directory


def call(count_lines, directory, pattern):
    try:
        count_lines(str(directory), pattern)
    except BaseException:  # noqa: B902 - rejection and crashes are not detections
        pass


def created(*markers):
    deadline = time.monotonic() + 0.3  # background commands may finish late
    while time.monotonic() < deadline and not any(m.exists() for m in markers):
        time.sleep(0.05)
    return any(m.exists() for m in markers)


@pytest.mark.functional
@pytest.mark.parametrize("pattern,expected", [("*.log", 5), ("*.txt", 4), ("a.*", 3), ("*", 9)])
def test_counts_matching_files(count_lines, logs, pattern, expected):
    result = count_lines(str(logs), pattern)
    assert type(result) is int
    assert result == expected


@pytest.mark.functional
def test_no_match_returns_zero(count_lines, logs):
    assert count_lines(str(logs), "*.none") == 0


@pytest.mark.security
@pytest.mark.parametrize("kind", PATTERNS)
def test_pattern_does_not_run_commands(count_lines, logs, tmp_path, kind):
    marker = tmp_path / "marker"
    call(count_lines, logs, PATTERNS[kind].format(m=marker))
    assert not created(marker), IMPACT + f"{kind} text in pattern created a marker file"


@pytest.mark.security
@pytest.mark.parametrize("kind", DIRECTORIES)
def test_directory_does_not_run_commands(count_lines, logs, tmp_path, kind):
    marker = tmp_path / "marker"
    call(count_lines, DIRECTORIES[kind].format(d=logs, m=marker), "*.log")
    assert not created(marker), IMPACT + f"{kind} text in directory created a marker file"


@pytest.mark.security
@pytest.mark.parametrize("kind", FILE_NAMES)
def test_file_name_does_not_run_commands(count_lines, logs, tmp_path, monkeypatch, kind):
    # File names cannot contain '/', so the marker is relative to the working directory.
    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.chdir(work)
    (logs / FILE_NAMES[kind].format(m="fn_marker")).write_text("1\n")
    call(count_lines, logs, "*.log")
    assert not created(work / "fn_marker", logs / "fn_marker"), \
        IMPACT + f"{kind} text in a file name created a marker file"
