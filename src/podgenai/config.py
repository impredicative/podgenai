import os
from pathlib import Path

from podgenai.util.dotenv_ import load_dotenv

load_dotenv()

CWD: Path = Path.cwd()
PACKAGE_PATH: Path = Path(__file__).parent
PACKAGE_NAME: str = PACKAGE_PATH.name
REPO_PATH: Path = PACKAGE_PATH.parent.parent

AUDIO_PATHS: dict[str, Path] = {p.stem: p for p in (PACKAGE_PATH / "audio").glob("*.mp3")}
GiB = 1024**3
MAX_CONCURRENT_WORKERS = int(os.environ.get("PODGENAI_OPENAI_MAX_WORKERS", str(16)))  # Note: Default value is documented in readme.
assert MAX_CONCURRENT_WORKERS >= 1
MAX_TEXT_LENGTH_IN_FILENAME: int = 50
NUM_SECTIONS_MIN: int = 3  # Applies only to the `max_sections` argument. Does not apply to LLM output.
NUM_SECTIONS_MAX: int = 100
PAUSE_BETWEEN_PARTS: float = 0.25  # In seconds.
PAUSE_BETWEEN_SUBTOPICS: float = 0.5  # In seconds.
PROMPTS: dict[str, str] = {p.stem: p.read_text().strip() for p in (PACKAGE_PATH / "prompts").glob("*.txt")}
WORK_PATH: Path = CWD / "work"
