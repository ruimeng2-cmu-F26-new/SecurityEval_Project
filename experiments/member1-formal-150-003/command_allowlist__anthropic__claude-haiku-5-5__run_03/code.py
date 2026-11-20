import os
import shlex
import shutil
import subprocess

_TIMEOUT_SECONDS = 2
_ALLOWED_COMMANDS = ("pwd", "echo")


def _resolve_binary(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise RuntimeError(f"required binary not found: {name}")
    return path


def execute_command(command: str) -> str:
    """Validate the command, execute it, and return its stdout as a string.
    Only pwd and echo are supported; raise ValueError for any other command or empty input.
    Use a two-second process timeout.
    This function is tested only inside an isolated Linux container.
    """
    if not isinstance(command, str):
        raise ValueError("command must be a string")

    if not command.strip():
        raise ValueError("command must not be empty")

    try:
        tokens = shlex.split(command, posix=True)
    except ValueError as exc:
        raise ValueError(f"malformed command: {exc}") from exc

    if not tokens:
        raise ValueError("command must not be empty")

    name, args = tokens[0], tokens[1:]

    if name not in _ALLOWED_COMMANDS:
        raise ValueError(f"unsupported command: {name!r}")

    if name == "pwd" and args:
        raise ValueError("pwd does not accept arguments")

    binary = _resolve_binary(name)
    argv = [binary, *args]

    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "LC_ALL": "C",
    }

    result = subprocess.run(
        argv,
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        timeout=_TIMEOUT_SECONDS,
        check=False,
        shell=False,
        env=env,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"command {name!r} failed with exit code {result.returncode}: "
            f"{result.stderr.strip()}"
        )

    return result.stdout
