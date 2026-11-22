import shlex
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
        raise ValueError("Command must be a string.")

    try:
        tokens = shlex.split(command)
    except ValueError as exc:
        raise ValueError(f"Invalid command syntax: {exc}") from exc

    if not tokens:
        raise ValueError("Empty command.")

    program = tokens[0]
    if program not in _ALLOWED_COMMANDS:
        raise ValueError(f"Unsupported command: {program!r}. Only 'pwd' and 'echo' are allowed.")

    if program == "pwd" and len(tokens) != 1:
        raise ValueError("The 'pwd' command does not accept arguments.")

    result = subprocess.run(
        tokens,
        capture_output=True,
        text=True,
        timeout=_TIMEOUT_SECONDS,
        check=False,
        shell=False,
    )
    return result.stdout
