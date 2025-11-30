from models import User, Repository
from typing import Optional
from sqlalchemy.orm import Session
from schemas import UserCreate, UserResponse, RepoCreate, RepoResponse
import bcrypt

def create_user(db : Session ,user : UserCreate) -> User:
    hashed = hash_pwd(user.password)
    actual_user=User(username=user.username, email=user.email, password_hash=hashed)
    db.add(actual_user)
    db.commit()
    db.refresh(actual_user)
    return actual_user

def get_user(db,user_id) -> Optional[User]:
    temp=db.query(User).filter(User.user_id==user_id).first()
    return temp

# ~~~
def create_repo(db,repo):
    actual_repo=Repository(reponame=repo.reponame, maintainer_id=repo.maintainer_id)
    db.add(actual_repo)
    db.commit()
    db.refresh(actual_repo)
    # chore: add a git operation to init a repo in tmp/repos
    return actual_repo

def get_repo_by_name(db,reponame) -> Optional[Repository]:
    temp=db.query(Repository).filter(Repository.reponame==reponame).first()
    return temp


def get_repo_by_id(db,repo_id) -> Optional[Repository]:
    temp=db.query(Repository).filter(Repository.repo_id==repo_id).first()
    return temp


# helper ~~~
def hash_pwd(plaintext: str) -> str:
    return bcrypt.hashpw(plaintext.encode(), bcrypt.gensalt()).decode()