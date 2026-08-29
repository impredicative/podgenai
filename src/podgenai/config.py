import os
from pathlib import Path

import jinja2

from podgenai.util.dotenv_ import load_dotenv
from podgenai.util.jinja2 import load_templates

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
PROMPTS: dict[str, jinja2.Template] = load_templates(PACKAGE_PATH / "prompts")
TTS_DISCLAIMER_WO_DOC: str = (
    "Both the text and audio in this media are AI-generated and may contain inaccurate or unintended content. The information presented has not been verified or researched, and should not be relied upon as factual or professional advice. Any resemblance or similarity to existing works is coincidental and unintended."
)
TTS_DISCLAIMER_W_DOC: str = "Both the text and audio in this media are AI-generated from the source documentation."
TTS_MONOLOGUE_TONE: str = "Speak naturally and conversationally, with a warm, confident tone, moderate pace, subtle emphasis, and restrained expressiveness, without sounding scripted or like an announcer."
VERIFY_PROMPT: bool = {"true": True, "false": False, "y": True, "n": False, "yes": True, "no": False, "1": True, "0": False}[os.environ.get("PODGENAI_VERIFY_PROMPT", "false").strip().lower()]
WORK_PATH: Path = CWD / "work"
