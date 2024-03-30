from pathlib import Path

import dotenv

dotenv.load_dotenv()

PACKAGE_PATH = Path(__file__).parent
REPO_PATH = PACKAGE_PATH.parent.parent
