import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Base backend directory
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent

# Load .env if present in backend or root
load_dotenv(BACKEND_DIR / ".env")
load_dotenv(PROJECT_ROOT / ".env")

# Path to the cloned AutoComment_Python repository
# Allows overriding via environment variable
CUSTOM_REPO_DIR = os.getenv("AUTOCOMMENT_REPO_DIR")
if CUSTOM_REPO_DIR:
    REPO_DIR = Path(CUSTOM_REPO_DIR).resolve()
else:
    # Try standard paths: root/AutoComment_Python, or sibling directory
    candidate_paths = [
        PROJECT_ROOT / "AutoComment_Python",
        PROJECT_ROOT.parent / "AutoComment_Python",
        BACKEND_DIR / "AutoComment_Python"
    ]
    REPO_DIR = next((p for p in candidate_paths if p.exists() and (p / "auto.py").exists()), candidate_paths[0])

AUTO_PY = REPO_DIR / "auto.py"
ACCOUNTS_FILE = REPO_DIR / "accounts" / "accounts.json"
COOKIES_DIR = REPO_DIR / "cookies"
RESULTS_FILE = REPO_DIR / "results.json"
REPO_ENV_FILE = REPO_DIR / ".env"

# Python interpreter to execute auto.py
# Default to current interpreter (which will be venv if uvicorn runs in venv)
PYTHON_BIN = sys.executable

# Server configs
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
DEFAULT_TIMEOUT_SECONDS = int(os.getenv("PROCESS_TIMEOUT_SECONDS", "600"))  # 10 minutes default
