import shlex
import shutil
import subprocess

_ALLOWED_COMMANDS = ("pwd", "echo")
_TIMEOUT_SECONDS = 2


def _resolve_binary(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise ValueError(f"Command not available on this system: {name}")
    return path


def execute_command(command: str) -> str:
    """Validate the command, execute it, and return its stdout as a string.

    Only pwd and echo are supported; raise ValueError for any other command
    or empty input. A two-second process timeout is enforced.
    """
    if not isinstance(command, str):
        raise ValueError("Command must be a string")

    if not command.strip():
        raise ValueError("Command must not be empty")

    try:
        tokens = shlex.split(command)
    except ValueError as exc:
        raise ValueError(f"Malformed command: {exc}") from exc

    if not tokens:
        raise ValueError("Command must not be empty")

    name, args = tokens[0], tokens[1:]

    if name not in _ALLOWED_COMMANDS:
        raise ValueError(f"Unsupported command: {name!r}")

    if name == "pwd" and args:
        raise ValueError("pwd does not accept arguments")

    binary = _resolve_binary(name)

    result = subprocess.run(
        [binary, *args],
        capture_output=True,
        text=True,
        timeout=_TIMEOUT_SECONDS,
        shell=False,
        stdin=subprocess.DEVNULL,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Command {name!r} failed with exit code {result.returncode}: "
            f"{result.stderr.strip()}"
        )

    return result.stdout
