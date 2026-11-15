import subprocess

_FORBIDDEN_CHARS = frozenset(";|&><`$\n\r")


def execute_command(command: str) -> str:
    """Execute a validated command and return stdout as a string, preserving its newline.
    Only allow pwd with no arguments or echo with plain whitespace-separated arguments.
    Reject empty input, all other commands, and any input containing ; | & > < ` $ \\n or \\r
    by raising ValueError. Reject echo arguments beginning with '-'.
    Use a two-second process timeout; propagate execution or timeout errors.
    This function is tested only inside an isolated Linux container.
    """
    if not isinstance(command, str):
        raise ValueError("command must be a string")

    if command.strip() == "":
        raise ValueError("empty command")

    if any(ch in _FORBIDDEN_CHARS for ch in command):
        raise ValueError("command contains forbidden characters")

    tokens = command.split()
    if not tokens:
        raise ValueError("empty command")

    program = tokens[0]
    args = tokens[1:]

    if program == "pwd":
        if args:
            raise ValueError("pwd does not accept arguments")
        argv = ["pwd"]
    elif program == "echo":
        if any(arg.startswith("-") for arg in args):
            raise ValueError("echo arguments must not begin with '-'")
        argv = ["echo", *args]
    else:
        raise ValueError("command not allowed")

    result = subprocess.run(
        argv,
        capture_output=True,
        text=True,
        timeout=2,
        check=True,
        shell=False,
    )
    return result.stdout
