import re
from pathlib import Path


def sanitize_filename(name: str) -> str:
    # replace spaces with underscores, strip forbidden filesystem chars
    name = name.strip().replace(" ", "_")
    # remove anything that's not alphanumeric, underscore, hyphen, or dot
    return re.sub(r"[^\w\-.]", "", name)

def is_noise_paragraph(text: str) -> bool:
    # match "*Small business" with optional space after *, case-insensitive
    if re.match(r"^\*\s*small business$", text.strip(), flags=re.IGNORECASE):
        return True
    return False

def load_processed_list(manifest_path: Path) -> set[str]:
    if manifest_path.exists():
        return {line.strip() for line in manifest_path.read_text(encoding="utf-8").splitlines() if line.strip()}
    return set()

def append_processed_file(manifest_path: Path, filename: str):
    with open(manifest_path, "a", encoding="utf-8") as f:
        f.write(filename + "\n")