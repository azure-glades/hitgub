from typing import Optional

from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session
from sqlalchemy import func
from math import ceil
from .models import User, Repository, Issue
from .json_dto import UserCreate, UserResponse, RepoCreate, RepoResponse, IssueCreate, IssueDetailResponse, IssuePage, IssueItem, PageMeta
from .git_ops import init_bare
from .mongo_store import create_issue_doc, add_comment, get_issue
import bcrypt

def create_user(db : Session ,user : UserCreate) -> User:
    hashed = hash_pwd(user.password)
    actual_user=User(username=user.username, email=user.email, password_hash=hashed)
    db.add(actual_user)
    db.commit()
    db.refresh(actual_user)
    return actual_user

def get_user_by_name(db,username) -> Optional[User]:
    return db.query(User).filter(User.username==username).first()

def get_user_by_id(db, user_id) -> Optional[User]:
    return db.query(User).filter(User.user_id==user_id).first()

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

# ~~~
def create_issue(db: Session,
                 repo_id: int,
                 author_id: int,
                 issue_in: IssueCreate) -> Issue:
    max_num = db.query(func.max(Issue.issue_num)).filter_by(repo_id=repo_id).scalar() or 0
    next_num = max_num + 1
    author_name = get_user_by_id(db, author_id).username
    db_issue = Issue(repo_id=repo_id, author_id=author_id, issue_num=next_num, title=issue_in.title)
    db.add(db_issue)
    db.flush()

    mongo_id = create_issue_doc(db_issue.issue_num, issue_in.title, issue_in.body, author_name)
    db_issue.nosql_thread_id = str(mongo_id)

    db.commit()
    db.refresh(db_issue)
    return db_issue

def append_comment(db: Session,
                   repo_id: int,
                   issue_num: int,
                   author_id: int,
                   body: str) -> Issue:
    try:
        issue_obj = db.query(Issue).filter_by(repo_id=repo_id,issue_num=issue_num).one()
    except NoResultFound as e:
        raise ValueError("Issue not found") from e

    author = db.query(User).filter_by(user_id=author_id).one()
    add_comment(issue_obj.nosql_thread_id, author.username, body)
    issue_obj.updated_at = func.now() # -> set last-updated field
    db.commit()
    db.refresh(issue_obj)
    return issue_obj

def get_issue_thread(db: Session,
                     repo_id: int,
                     issue_num: int) -> IssueDetailResponse:
    try:
        issue_obj = db.query(Issue).filter_by(repo_id=repo_id,issue_num=issue_num).one()
    except NoResultFound as e:
        raise ValueError("Issue not found") from e
    thread_doc = get_issue(issue_obj.nosql_thread_id)
    return IssueDetailResponse(
        repo_id=repo_id,
        issue_num=issue_num,
        title=issue_obj.title,
        author_id=issue_obj.author_id,
        body=thread_doc['body'],
        created_at=issue_obj.created_at,
        comments=thread_doc['comments']
    )

def list_issues(db: Session,
                repo_id: int,
                page: int = 1,
                size: int = 20) -> IssuePage:
    offset = (page - 1) * size
    total = db.query(func.count(Issue.issue_num)).filter_by(repo_id=repo_id).scalar()
    rows = (db.query(Issue)
              .filter_by(repo_id=repo_id)
              .order_by(Issue.created_at.desc())
              .offset(offset)
              .limit(size)
              .all())
    pages = ceil(total / size) if total else 1
    return IssuePage(
        meta=PageMeta(page=page, size=size, total_size=total, total_pages=pages),
        items=[IssueItem.model_validate(r) for r in rows]
    )