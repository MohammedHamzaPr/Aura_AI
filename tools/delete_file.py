from pathlib import Path

WORKSPACE = Path(__file__).parent.parent / "workspace"


def delete_file(path: str) -> str:
    file_path = (WORKSPACE / path).resolve()

    if not file_path.is_relative_to(WORKSPACE.resolve()):
        raise PermissionError("Access outside workspace is not allowed.")

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if not file_path.is_file():
        raise IsADirectoryError("Only files can be deleted.")

    file_path.unlink()

    return f"File deleted successfully: {path}"