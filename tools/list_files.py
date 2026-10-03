from pathlib import Path

WORKSPACE = Path(__file__).parent.parent / "workspace"


def list_files(path: str = ".") -> list[str]:
    directory = (WORKSPACE / path).resolve()

    if not directory.is_relative_to(WORKSPACE.resolve()):
        raise PermissionError("Access outside workspace is not allowed.")

    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {path}")

    if not directory.is_dir():
        raise NotADirectoryError(f"Not a directory: {path}")

    return [
        str(item.relative_to(WORKSPACE))
        for item in directory.iterdir()
    ]