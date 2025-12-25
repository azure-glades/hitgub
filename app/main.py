import sqlalchemy
import traceback
import logging
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from . import models, json_dto, crud
from .crud import get_issue_thread
from .dependency_injector import get_db, fake_current_user
from .database_sessions import engine

from .json_dto import RepoCreate, IssueCreate, CommentCreate, IssueDetailResponse, IssuePage

app = FastAPI(title="Private Repo Manager")
models.Base.metadata.create_all(bind=engine)
logger = logging.getLogger(__name__)


# repo endpoints
# making new repository
@app.post("/repos", response_model=json_dto.RepoResponse, tags=["repos"])
def init_repo(payload: RepoCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_repo(db=db, repo_in=payload)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.exception("An unhandled error occurred while creating a repo")
        raise HTTPException(status_code=500, detail="Internal server error")



# Issues Endpoints
# making new issue
@app.post("/repos/{repo_id}/issues", response_model=json_dto.IssueResponse, tags=["repos"])
def new_issue(repo_id: int,
              payload: IssueCreate,
              current_user_id: int = Depends(fake_current_user),
              db: Session = Depends(get_db)):
    return crud.create_issue(db=db, repo_id=repo_id, author_id=current_user_id, issue_in=payload)

# adding a comment to issue
@app.post("/repos/{repo_id}/issues/{issue_num}/comments")
def add_comment(repo_id: int,
                issue_num: int,
                payload: CommentCreate,
                current_user_id: int = Depends(fake_current_user),
                db: Session = Depends(get_db)):
    crud.append_comment(db, repo_id, issue_num, current_user_id, payload.body)
    return {"reply": "comment added"}

# opening and viewing an issue thread
@app.get("/repos/{repo_id}/issues/{issue_num}", response_model=IssueDetailResponse)
def read_issue(repo_id: int,
               issue_num: int,
               db: Session = Depends(get_db)):
    return get_issue_thread(db, repo_id, issue_num)
# view all issue
@app.get("/repos/{repo_id}/issues", response_model=IssuePage)
def read_issues(repo_id: int,
                page: int = Query(1, ge=1),
                size: int = Query(20, ge=1, le=100),
                db: Session = Depends(get_db)):
    return crud.list_issues(db, repo_id, page, size)


# User endpoints
# making new users
@app.post("/users", response_model=json_dto.UserResponse, tags=["users"])
def create_user(user: json_dto.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_name(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username exists")
    return crud.create_user(db, user)

@app.get("/health")
def health_check():
    return {"status": "ok"}