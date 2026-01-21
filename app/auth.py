import secrets
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
import bcrypt

from . import crud, models
from .dependency_injector import get_db

security = HTTPBasic()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def authenticate_user(db: Session, username: str, password: str):
    user = crud.get_user_by_name(db, username)
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user

def get_current_user(credentials: HTTPBasicCredentials = Depends(security), db: Session = Depends(get_db)):
    user = authenticate_user(db, credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user

def verify_repo_access(repo_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Dependency to check if user has access to a specific repo_id (from path)."""
    # Note: This requires repo_id to be a path parameter with exact name 'repo_id'
    if not crud.check_user_repo_access(db, user.user_id, repo_id):
         raise HTTPException(status_code=403, detail="Access denied to repository")
    return user

# For Git operations, the repo name is in the path, we need to resolve it to ID
def verify_git_access(repo_name: str, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Dependency for Git operations. 
    1. Resolves repo_name to repo_id. 
    2. Checks if user has access to that repo.
    """
    repo = crud.get_repo_by_name(db, repo_name)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    if not crud.check_user_repo_access(db, user.user_id, repo.repo_id):
        raise HTTPException(status_code=403, detail="Access denied to repository")
    
    return user
