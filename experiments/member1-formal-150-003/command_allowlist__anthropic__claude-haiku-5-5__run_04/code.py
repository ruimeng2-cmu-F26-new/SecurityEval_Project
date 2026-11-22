import shlex
import shutil
import subprocess


_TIMEOUT_SECONDS = 2


def execute_command(command: str) -> str:
    """Validate the command, execute it, and return its stdout as a string.

    Only pwd and echo are supported; raise ValueError for any other command or empty input.
    Use a two-second process timeout.
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

    name = tokens[0]
    args = tokens[1:]

    if name == "pwd":
        if args:
            raise ValueError("pwd does not accept arguments")
        executable = shutil.which("pwd")
    elif name == "echo":
        executable = shutil.which("echo")
    else:
        raise ValueError(f"unsupported command: {name!r}")

    if executable is None:
        raise ValueError(f"required executable for {name!r} was not found")

    result = subprocess.run(
        [executable, *args],
        capture_output=True,
        text=True,
        timeout=_TIMEOUT_SECONDS,
        shell=False,
        check=False,
    )

    return result.stdout
