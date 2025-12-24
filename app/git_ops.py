from pathlib import Path
from git import Repo
import os

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR / "tmp" / "repos"

def init_bare(repo_name: str) -> Path:
    repo_path = REPO_ROOT / f"{repo_name}.git"
    repo_path.parent.mkdir(parents=True, exist_ok=True)
    if repo_path.exists():
        raise FileExistsError("Bare repo already exists")
    Repo.init(repo_path, bare=True)
    return repo_path.resolve()