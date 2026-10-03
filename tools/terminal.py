import os
import shlex
import subprocess
from pathlib import Path


WORKSPACE = (Path(__file__).parent.parent / "workspace").resolve()


def _path_is_inside_workspace(path: Path) -> bool:
    try:
        path.resolve().relative_to(WORKSPACE)
        return True
    except ValueError:
        return False


def _check_command_paths(command: str) -> None:
    """
    Basic protection against explicit Windows paths
    outside the AURA workspace.
    """

    forbidden_roots = [
        "C:\\Windows",
        "C:\\Program Files",
        "C:\\Program Files (x86)",
        "C:\\Users"
    ]

    command_lower = command.lower()

    for root in forbidden_roots:
        if root.lower() in command_lower:
            raise PermissionError(
                f"Access outside AURA workspace is blocked: {root}"
            )


def run_command(command: str) -> str:

    if not command or not command.strip():
        return "Error: Empty command."

    try:
        _check_command_paths(command)

        result = subprocess.run(
            command,
            shell=True,
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            timeout=30
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        return (
            f"Exit code: {result.returncode}\n"
            f"STDOUT:\n{stdout}\n"
            f"STDERR:\n{stderr}"
        )

    except PermissionError as error:
        return f"Permission denied: {error}"

    except subprocess.TimeoutExpired:
        return "Command timed out after 30 seconds."

    except Exception as error:
        return f"Terminal error: {error}"
