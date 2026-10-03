from pathlib import Path

WORKSPACE = Path(__file__).parent.parent / "workspace"


def write_file(path: str, content: str) -> str:
    file_path = (WORKSPACE / path).resolve()

    if not file_path.is_relative_to(WORKSPACE.resolve()):
        raise PermissionError("Access outside workspace is not allowed.")

    file_path.parent.mkdir(parents=True, exist_ok=True)

    file_path.write_text(content, encoding="utf-8")

    return f"File written successfully: {path}"