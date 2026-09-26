import os
from pathlib import Path
from typing import Final

import jinja2

from podgenai.util.dotenv_ import load_dotenv
from podgenai.util.jinja2 import load_templates

load_dotenv()

CWD: Final[Path] = Path.cwd()
PACKAGE_PATH: Final[Path] = Path(__file__).parent
PACKAGE_NAME: Final[str] = PACKAGE_PATH.name
REPO_PATH: Final[Path] = PACKAGE_PATH.parent.parent

AUDIO_PATHS: Final[dict[str, Path]] = {p.stem: p for p in (PACKAGE_PATH / "audio").glob("*.mp3")}
GiB: Final[int] = 1024**3
MAX_CONCURRENT_WORKERS: Final[int] = int(os.environ.get("PODGENAI_OPENAI_MAX_WORKERS", str(16)))  # Note: Default value is documented in readme.
assert MAX_CONCURRENT_WORKERS >= 1
MAX_TEXT_LENGTH_IN_FILENAME: Final[int] = 50
NUM_SECTIONS_MIN: Final[int] = 3  # Applies only to the `max_sections` argument. Does not apply to LLM output.
NUM_SECTIONS_MAX: Final[int] = 100
PAUSE_BETWEEN_PARTS: Final[float] = 0.25  # In seconds.
PAUSE_BETWEEN_SUBTOPICS: Final[float] = 0.5  # In seconds.
PROMPTS: Final[dict[str, jinja2.Template]] = load_templates(PACKAGE_PATH / "prompts")
TTS_DISCLAIMER_WO_DOC: Final[str] = (
    "Both the text and audio in this media are AI-generated and may contain inaccurate or unintended content. The information presented has not been verified or researched, and should not be relied upon as factual or professional advice. Any resemblance or similarity to existing works is coincidental and unintended."
)
TTS_DISCLAIMER_W_DOC: Final[str] = "Both the text and audio in this media are AI-generated from the source documentation."
TTS_MONOLOGUE_TONE: Final[str] = "Speak naturally and conversationally, with a warm, confident tone, moderate pace, subtle emphasis, and restrained expressiveness, without sounding scripted or like an announcer."
VERIFY_PROMPT: Final[bool] = {"true": True, "false": False, "y": True, "n": False, "yes": True, "no": False, "1": True, "0": False}[os.environ.get("PODGENAI_VERIFY_PROMPT", "false").strip().lower()]
WORK_PATH: Final[Path] = CWD / "work"
