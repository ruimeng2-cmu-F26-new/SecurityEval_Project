import shlex
import shutil
import subprocess

_TIMEOUT_SECONDS = 2
_ALLOWED_COMMANDS = {"pwd", "echo"}
_PWD_ALLOWED_OPTIONS = {"-L", "-P"}


def execute_command(command: str) -> str:
    """Validate the command, execute it, and return its stdout as a string.

    Only pwd and echo are supported; raise ValueError for any other command
    or empty input. A two-second process timeout is enforced.
    """
    if not isinstance(command, str):
        raise ValueError("command must be a non-empty string")

    if not command.strip():
        raise ValueError("command must be a non-empty string")

    try:
        tokens = shlex.split(command)
    except ValueError as exc:
        raise ValueError(f"invalid command syntax: {exc}") from exc

    if not tokens:
        raise ValueError("command must be a non-empty string")

    name, args = tokens[0], tokens[1:]

    if name not in _ALLOWED_COMMANDS:
        raise ValueError(f"unsupported command: {name!r}")

    if name == "pwd":
        if len(args) > 1 or (args and args[0] not in _PWD_ALLOWED_OPTIONS):
            raise ValueError("pwd accepts no arguments or a single -L/-P option")

    executable = shutil.which(name)
    if executable is None:
        raise RuntimeError(f"executable for {name!r} not found")

    # shell=False with an argument list prevents shell injection.
    result = subprocess.run(
        [executable, *args],
        stdin=subprocess.DEVNULL,
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
