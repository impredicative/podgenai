from pathlib import Path

import dotenv

dotenv.load_dotenv()

PACKAGE_PATH: Path = Path(__file__).parent
REPO_PATH: Path = PACKAGE_PATH.parent.parent

PROMPTS: dict[str, str] = {p.stem: p.read_text().strip() for p in (REPO_PATH / 'prompts').glob('*.txt')}
