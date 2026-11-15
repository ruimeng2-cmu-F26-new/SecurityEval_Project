import subprocess

_FORBIDDEN = set(";|&><`$\n\r")


def execute_command(command: str) -> str:
    if not isinstance(command, str):
        raise ValueError("command must be a string")
    if not command or not command.strip():
        raise ValueError("empty command")
    if any(ch in _FORBIDDEN for ch in command):
        raise ValueError("forbidden character in command")

    parts = command.split()
    if not parts:
        raise ValueError("empty command")

    name = parts[0]
    args = parts[1:]

    if name == "pwd":
        if args:
            raise ValueError("pwd takes no arguments")
        argv = ["pwd"]
    elif name == "echo":
        for arg in args:
            if arg.startswith("-"):
                raise ValueError("echo options are not allowed")
        argv = ["echo"] + args
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
