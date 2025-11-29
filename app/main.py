from fastapi import FastAPI
import git

app = FastAPI(title="Private Repo Manager")

@app.post("/repos/{repo_name}/init", tags=["git"])
def init_repo(repo_name: str):
    """Spring @RestController + @PostMapping equivalent"""
    path = f"tmp/repos/{repo_name}.git"
    git.Repo.init(path, bare=True)
    return {"status": "created", "path": path}

@app.get("/health")
def health_check():
    return {"status": "ok"}