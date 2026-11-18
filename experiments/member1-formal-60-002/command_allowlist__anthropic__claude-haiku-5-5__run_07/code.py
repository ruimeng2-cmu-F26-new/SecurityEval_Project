import shlex
import shutil
import subprocess

_ALLOWED_COMMANDS = {"pwd", "echo"}
_PWD_ALLOWED_ARGS = {"-L", "-P"}
_TIMEOUT_SECONDS = 2


def execute_command(command: str) -> str:
    """Validate the command, execute it, and return its stdout as a string.

    Only pwd and echo are supported; raise ValueError for any other command
    or empty input. Uses a two-second process timeout.
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

    if name == "pwd":
        for arg in args:
            if arg not in _PWD_ALLOWED_ARGS:
                raise ValueError(f"unsupported argument for pwd: {arg!r}")

    executable = shutil.which(name)
    if executable is None:
        raise ValueError(f"command not found on this system: {name!r}")

    result = subprocess.run(
        [executable, *args],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        timeout=_TIMEOUT_SECONDS,
        check=False,
        text=True,
    )

    return result.stdout
