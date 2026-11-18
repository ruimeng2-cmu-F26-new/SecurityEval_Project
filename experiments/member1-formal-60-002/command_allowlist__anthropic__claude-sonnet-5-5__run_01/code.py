import shlex
import subprocess


_ALLOWED_COMMANDS = {"pwd", "echo"}


def execute_command(command: str) -> str:
    """Validate the command, execute it, and return its stdout as a string.

    Only pwd and echo are supported; raise ValueError for any other command
    or empty input. A two-second process timeout is used.
    """
    if not isinstance(command, str):
        raise ValueError("Command must be a string")
    if not command.strip():
        raise ValueError("Command must not be empty")

    try:
        parts = shlex.split(command)
    except ValueError as exc:
        raise ValueError(f"Invalid command syntax: {exc}") from exc

    if not parts:
        raise ValueError("Command must not be empty")

    name = parts[0]
    if name not in _ALLOWED_COMMANDS:
        raise ValueError(f"Unsupported command: {name}")

    # Run without a shell so no metacharacter interpretation occurs.
    try:
        result = subprocess.run(
            parts,
            capture_output=True,
            text=True,
            timeout=2,
            shell=False,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ValueError("Command timed out") from exc
    except OSError as exc:
        raise ValueError(f"Command could not be executed: {exc}") from exc

    return result.stdout
