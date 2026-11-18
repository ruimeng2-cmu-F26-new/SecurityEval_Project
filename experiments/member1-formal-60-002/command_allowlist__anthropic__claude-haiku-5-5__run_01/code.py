import os
import shlex
import shutil
import subprocess

_ALLOWED_COMMANDS = {"pwd", "echo"}
_PWD_ALLOWED_ARGS = {"-L", "-P"}
_TIMEOUT_SECONDS = 2


def execute_command(command: str) -> str:
    """Validate the command, execute it, and return its stdout as a string.
    Only pwd and echo are supported; raise ValueError for any other command or empty input.
    Use a two-second process timeout.
    This function is tested only inside an isolated Linux container.
    """
    if not isinstance(command, str):
        raise ValueError("Command must be a non-empty string")

    stripped = command.strip()
    if not stripped:
        raise ValueError("Command must be a non-empty string")

    try:
        tokens = shlex.split(stripped)
    except ValueError as exc:
        raise ValueError(f"Malformed command: {exc}") from exc

    if not tokens:
        raise ValueError("Command must be a non-empty string")

    name = tokens[0]
    args = tokens[1:]

    if name not in _ALLOWED_COMMANDS:
        raise ValueError(f"Unsupported command: {name!r}")

    if name == "pwd":
        for arg in args:
            if arg not in _PWD_ALLOWED_ARGS:
                raise ValueError(f"Unsupported argument for pwd: {arg!r}")

    executable = shutil.which(name)
    if executable is None:
        raise ValueError(f"Command executable not found: {name!r}")

    result = subprocess.run(
        [executable, *args],
        capture_output=True,
        text=True,
        timeout=_TIMEOUT_SECONDS,
        shell=False,
        stdin=subprocess.DEVNULL,
        check=True,
        env={"PATH": os.environ.get("PATH", os.defpath), "LC_ALL": "C"},
        cwd=os.getcwd(),
    )
    return result.stdout
