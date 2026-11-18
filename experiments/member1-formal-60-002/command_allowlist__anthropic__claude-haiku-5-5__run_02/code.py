import shlex
import shutil
import subprocess

_ALLOWED_COMMANDS = {"pwd", "echo"}
_TIMEOUT_SECONDS = 2


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

    # shlex.split raises ValueError on malformed input (e.g. unbalanced quotes).
    tokens = shlex.split(command)
    if not tokens:
        raise ValueError("command must not be empty")

    name = tokens[0]
    args = tokens[1:]

    if name not in _ALLOWED_COMMANDS:
        raise ValueError(f"unsupported command: {name!r}")

    if name == "pwd" and args:
        raise ValueError("pwd does not accept arguments")

    executable = shutil.which(name)
    if executable is None:
        raise ValueError(f"command not available: {name!r}")

    # shell=False and an argument list ensure no shell interpretation occurs.
    result = subprocess.run(
        [executable, *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=_TIMEOUT_SECONDS,
        shell=False,
        check=False,
    )

    return result.stdout
