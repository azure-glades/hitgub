from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from . import models, json_dto, crud
from .dependency_injector import get_db
from .database_sessions import engine
import git

app = FastAPI(title="Private Repo Manager")
models.Base.metadata.create_all(bind=engine)

@app.post("/repos/{repo_name}/init", tags=["git"])
def init_repo(repo_name: str):
    """Spring @RestController + @PostMapping equivalent"""
    path = f"tmp/repos/{repo_name}.git"
    git.Repo.init(path, bare=True)
    return {"status": "created", "path": path}

@app.post("/users", response_model=json_dto.UserResponse, tags=["users"])
def create_user(user: json_dto.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username exists")
    return crud.create_user(db, user)

@app.get("/health")
def health_check():
    return {"status": "ok"}