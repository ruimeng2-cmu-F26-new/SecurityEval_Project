import shlex
import shutil
import subprocess

_ALLOWED_COMMANDS = ("pwd", "echo")
_TIMEOUT_SECONDS = 2


def execute_command(command: str) -> str:
    """Validate the command, execute it, and return its stdout as a string.

    Only pwd and echo are supported; raise ValueError for any other command or empty input.
    pwd accepts no arguments. echo accepts any arguments.
    Commands are executed without a shell, and a two-second process timeout is applied.
    """
    if not isinstance(command, str):
        raise ValueError("command must be a string")

    stripped = command.strip()
    if not stripped:
        raise ValueError("command must not be empty")

    try:
        tokens = shlex.split(stripped)
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
        raise ValueError(f"command not available on this system: {name!r}")

    result = subprocess.run(
        [executable, *args],
        capture_output=True,
        text=True,
        timeout=_TIMEOUT_SECONDS,
        check=False,
        shell=False,
    )
    return result.stdout
