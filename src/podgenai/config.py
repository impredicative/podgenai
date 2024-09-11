import os
from pathlib import Path

from podgenai.util.dotenv_ import load_dotenv

load_dotenv()

CWD: Path = Path.cwd()
PACKAGE_PATH: Path = Path(__file__).parent
REPO_PATH: Path = PACKAGE_PATH.parent.parent

GiB = 1024**3
MAX_CONCURRENT_WORKERS = int(os.environ.get("PODGENAI_OPENAI_MAX_WORKERS", 16))  # Note: Default value is documented in readme.
assert MAX_CONCURRENT_WORKERS >= 1
PROMPTS: dict[str, str] = {p.stem: p.read_text().strip() for p in (PACKAGE_PATH / "prompts").glob("*.txt")}
WORK_PATH: Path = CWD / "work"
