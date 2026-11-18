import shlex
import subprocess


def execute_command(command: str) -> str:
    """Validate the command, execute it, and return its stdout as a string.
    Only pwd and echo are supported; raise ValueError for any other command or empty input.
    Use a two-second process timeout.
    This function is tested only inside an isolated Linux container.
    """
    if not isinstance(command, str):
        raise ValueError("command must be a string")

    stripped = command.strip()
    if not stripped:
        raise ValueError("empty command")

    try:
        tokens = shlex.split(stripped)
    except ValueError as exc:
        raise ValueError(f"invalid command syntax: {exc}") from exc

    if not tokens:
        raise ValueError("empty command")

    name, args = tokens[0], tokens[1:]

    if name == "pwd":
        if args:
            raise ValueError("pwd does not accept arguments")
        argv = ["pwd"]
    elif name == "echo":
        argv = ["echo", *args]
    else:
        raise ValueError(f"unsupported command: {name!r}")

    result = subprocess.run(
        argv,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=2,
        check=True,
        shell=False,
    )
    return result.stdout
