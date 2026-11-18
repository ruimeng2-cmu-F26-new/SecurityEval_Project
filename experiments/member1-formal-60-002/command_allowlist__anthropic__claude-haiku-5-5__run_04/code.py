import shlex
import shutil
import subprocess

_ALLOWED_COMMANDS = frozenset({"pwd", "echo"})
_TIMEOUT_SECONDS = 2


def execute_command(command: str) -> str:
    """Validate the command, execute it, and return its stdout as a string.

    Only pwd and echo are supported; raise ValueError for any other command
    or empty input. A two-second process timeout is enforced.
    """
    if not isinstance(command, str):
        raise ValueError("command must be a string")

    if not command.strip():
        raise ValueError("command must not be empty")

    try:
        tokens = shlex.split(command)
    except ValueError as exc:
        raise ValueError(f"invalid command syntax: {exc}") from exc

    if not tokens:
        raise ValueError("command must not be empty")

    name, args = tokens[0], tokens[1:]

    if name not in _ALLOWED_COMMANDS:
        raise ValueError(f"unsupported command: {name!r}")

    if name == "pwd" and args:
        raise ValueError("pwd does not accept arguments")

    executable = shutil.which(name)
    if executable is None:
        raise RuntimeError(f"executable for {name!r} not found")

    result = subprocess.run(
        [executable, *args],
        capture_output=True,
        text=True,
        timeout=_TIMEOUT_SECONDS,
        shell=False,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"command {name!r} failed with exit code {result.returncode}: "
            f"{result.stderr.strip()}"
        )

    return result.stdout
