import sqlalchemy
import traceback
import logging
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from . import models, json_dto, crud
from .dependency_injector import get_db
from .database_sessions import engine

from .json_dto import RepoCreate

app = FastAPI(title="Private Repo Manager")
models.Base.metadata.create_all(bind=engine)
logger = logging.getLogger(__name__)

@app.post("/repos", response_model=json_dto.RepoResponse, tags=["repos"])
def init_repo(payload: RepoCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_repo(db=db, repo_in=payload)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.exception("An unhandled error occurred while creating a repo")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/users", response_model=json_dto.UserResponse, tags=["users"])
def create_user(user: json_dto.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username exists")
    return crud.create_user(db, user)

@app.get("/health")
def health_check():
    return {"status": "ok"}