from typing import Optional
from sqlalchemy.orm import Session

from .models import User, Repository
from .json_dto import UserCreate, UserResponse, RepoCreate, RepoResponse
from .git_ops import init_bare
import bcrypt

def create_user(db : Session ,user : UserCreate) -> User:
    hashed = hash_pwd(user.password)
    actual_user=User(username=user.username, email=user.email, password_hash=hashed)
    db.add(actual_user)
    db.commit()
    db.refresh(actual_user)
    return actual_user

def get_user(db,username) -> Optional[User]:
    return db.query(User).filter(User.username==username).first()

# ~~~
def create_repo(db: Session, repo_in: RepoCreate) -> Repository:
    db_repo = Repository(
        reponame=repo_in.reponame,
        maintainer_id=repo_in.maintainer_id
    )
    try:
        init_bare(db_repo.reponame)
    except FileExistsError:
        raise ValueError("Repository folder already exists on disk")
    try:
        db.add(db_repo)
        db.commit()
        db.refresh(db_repo)
        return db_repo
    except Exception as e:
        db.rollback()
        raise e

def get_repo_by_name(db,reponame) -> Optional[Repository]:
    temp=db.query(Repository).filter(Repository.reponame==reponame).first()
    return temp


def get_repo_by_id(db,repo_id) -> Optional[Repository]:
    temp=db.query(Repository).filter(Repository.repo_id==repo_id).first()
    return temp


# helper ~~~
def hash_pwd(plaintext: str) -> str:
    return bcrypt.hashpw(plaintext.encode(), bcrypt.gensalt()).decode()