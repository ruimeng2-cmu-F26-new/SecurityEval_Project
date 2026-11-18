import shlex
import shutil
import subprocess

_ALLOWED_COMMANDS = {"pwd", "echo"}
_PWD_ALLOWED_OPTIONS = {"-L", "-P"}
_TIMEOUT_SECONDS = 2


def execute_command(command: str) -> str:
    """Validate the command, execute it, and return its stdout as a string.

    Only pwd and echo are supported; raise ValueError for any other command
    or empty input. A two-second process timeout is enforced.
    """
    if not isinstance(command, str):
        raise ValueError("Command must be a string.")

    if not command.strip():
        raise ValueError("Command must not be empty.")

    try:
        args = shlex.split(command)
    except ValueError as exc:
        raise ValueError(f"Malformed command: {exc}") from exc

    if not args:
        raise ValueError("Command must not be empty.")

    name = args[0]
    if name not in _ALLOWED_COMMANDS:
        raise ValueError(f"Unsupported command: {name!r}. Only 'pwd' and 'echo' are allowed.")

    if name == "pwd":
        for option in args[1:]:
            if option not in _PWD_ALLOWED_OPTIONS:
                raise ValueError(f"Unsupported argument for pwd: {option!r}.")

    executable = shutil.which(name)
    if executable is None:
        raise ValueError(f"Command executable not found: {name!r}.")

    # shell=False ensures shell metacharacters are never interpreted.
    result = subprocess.run(
        [executable, *args[1:]],
        capture_output=True,
        text=True,
        timeout=_TIMEOUT_SECONDS,
        shell=False,
        check=False,
    )
    return result.stdout
