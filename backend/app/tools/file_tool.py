"""file_tool.py — read/write local files. write_file is also how the final report is persisted."""
import os


def read_file(filename: str) -> str:
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()[:5000]
    except Exception as e:
        return f"[read_file error] {e}"


def write_file(filename: str, content: str) -> str:
    os.makedirs("data/reports", exist_ok=True)
    path = os.path.join("data/reports", filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path
