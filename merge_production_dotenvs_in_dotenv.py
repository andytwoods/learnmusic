# ruff: noqa
import os
from collections.abc import Sequence
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
PRODUCTION_DOTENVS_DIR = BASE_DIR / ".envs" / ".production"
PRODUCTION_DOTENV_FILES = [
    PRODUCTION_DOTENVS_DIR / ".django",
    PRODUCTION_DOTENVS_DIR / ".postgres",
]
DOTENV_FILE = BASE_DIR / ".env"


def merge(
    output_file: Path,
    files_to_merge: Sequence[Path],
) -> None:
    """Merge dotenv-like files with consistent LF newlines and no extra blank lines.

    - Normalizes all inputs to use "\n" line endings regardless of OS.
    - Ensures exactly one trailing newline per merged file chunk.
    - Avoids introducing extra blank lines between merged files.
    """
    merged_chunks: list[str] = []
    for merge_file in files_to_merge:
        # Normalize to LF newlines, then ensure a single trailing newline
        text = merge_file.read_text()
        # Convert CRLF/CR to LF for consistency
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # Append the content as-is, then add exactly one extra separator newline
        merged_chunks.append(text + "\n")

    # Join chunks without adding extra separators (each chunk already ends with one \n)
    merged_content = "".join(merged_chunks)
    output_file.write_text(merged_content)


if __name__ == "__main__":
    merge(DOTENV_FILE, PRODUCTION_DOTENV_FILES)
