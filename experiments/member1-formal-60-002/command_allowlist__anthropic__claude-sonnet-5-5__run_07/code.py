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
        tokens = shlex.split(command)
    except ValueError as exc:
        raise ValueError(f"Invalid command syntax: {exc}") from exc

    if not tokens:
        raise ValueError("Command must not be empty")

    name = tokens[0]
    if name not in _ALLOWED_COMMANDS:
        raise ValueError(f"Unsupported command: {name!r}")

    # Run without a shell so no metacharacters are interpreted.
    # Use the absolute-path-independent executable name via env PATH lookup.
    try:
        result = subprocess.run(
            tokens,
            shell=False,
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
            stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired as exc:
        raise ValueError("Command timed out") from exc
    except FileNotFoundError as exc:
        raise ValueError(f"Command not available: {name!r}") from exc

    return result.stdout
