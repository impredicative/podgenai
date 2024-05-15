import os
from pathlib import Path

import dotenv

dotenv.load_dotenv()

CWD: Path = Path.cwd()
PACKAGE_PATH: Path = Path(__file__).parent
REPO_PATH: Path = PACKAGE_PATH.parent.parent

GiB = 1024**3
# DISKCACHE_PATH = REPO_PATH / ".diskcache"
# DISKCACHE_SIZE_LIMIT = 1 * GiB
# DISKCACHE = diskcache.FanoutCache(directory=str(DISKCACHE_PATH), timeout=1, size_limit=DISKCACHE_SIZE_LIMIT)
MAX_CONCURRENT_WORKERS = int(os.environ.get("PODGENAI_OPENAI_MAX_WORKERS", 16))  # Note: Default value is documented in readme.
assert MAX_CONCURRENT_WORKERS >= 1
PROMPTS: dict[str, str] = {p.stem: p.read_text().strip() for p in (PACKAGE_PATH / "prompts").glob("*.txt")}
WORK_PATH: Path = CWD / "work"
