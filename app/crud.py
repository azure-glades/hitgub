from typing import Optional

from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session
from sqlalchemy import func, delete
from math import ceil
from .models import User, Repository, Issue, Role, user_repo_roles, UserTier
from .json_dto import UserCreate, UserResponse, RepoCreate, RepoResponse, IssueCreate, IssueDetailResponse, IssuePage, IssueItem, PageMeta, RepoPage, RepoItem, UserItem, UserPage, UserTierUpdate, AccessLogItem, AccessLogPage
from .models import AccessLog, Action
from .git_ops import init_bare
from .mongo_store import create_issue_doc, add_comment, get_issue
import bcrypt

def create_user(db : Session ,user : UserCreate, tier: UserTier = UserTier.developer) -> User:
    hashed = hash_pwd(user.password)
    actual_user=User(username=user.username, email=user.email, password_hash=hashed, tier= tier)
    db.add(actual_user)
    db.commit()
    db.refresh(actual_user)
    return actual_user

def get_user_by_name(db,username) -> Optional[User]:
    return db.query(User).filter(User.username==username).first()

def get_user_by_id(db, user_id) -> Optional[User]:
    return db.query(User).filter(User.user_id==user_id).first()

def list_users(db: Session, page: int = 1, size: int = 20) -> UserPage:
    offset = (page - 1) * size
    total = db.query(func.count(User.user_id)).scalar()
    rows = (db.query(User)
              .order_by(User.user_id.desc())
              .offset(offset)
              .limit(size)
              .all())
    pages = ceil(total / size) if total else 1
    return UserPage(
        meta=PageMeta(page=page, size=size, total_size=total, total_pages=pages),
        items=[
            UserItem(
                    user_id=r.user_id,
                    username=r.username,
                    email=r.email,
                    tier=r.tier.value          # enum → string
            )
            for r in rows
        ]
    )

def change_user_tier(db: Session, user_id: int, new_tier: UserTier) -> User:
    if user_id == 1 and new_tier != UserTier.admin:
        raise ValueError("Cannot demote root user")
    
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user:
        raise ValueError("User not found")
    user.tier = new_tier
    db.commit()
    db.refresh(user)
    return user
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

def list_repos(db: Session, page: int = 1, size: int = 20) -> RepoPage:
    offset = (page - 1) * size
    total  = db.query(func.count(Repository.repo_id)).scalar()
    rows   = (db.query(Repository, User.username)
                .join(User, User.user_id == Repository.maintainer_id)
                .order_by(Repository.repo_id.desc())
                .offset(offset)
                .limit(size)
                .all())

    pages = ceil(total / size) if total else 1

    return RepoPage(
        meta=PageMeta(page=page, size=size, total_size=total, total_pages=pages),
        items=[
            RepoItem(
                repo_id=repo.repo_id,
                reponame=repo.reponame,
                maintainer_name=username,
                maintainer_id=repo.maintainer_id
            )
            for repo, username in rows
        ]
    )

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
        author=issue_obj.author.username if issue_obj.author else "Unknown",
        body=thread_doc['body'],
        status=issue_obj.status.value,
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
    
    # Build items with author username
    items = []
    for issue in rows:
        item_dict = {
            "issue_num": issue.issue_num,
            "title": issue.title or "",
            "author_id": issue.author_id,
            "author": issue.author.username if issue.author else "Unknown",
            "status": issue.status.value,
            "created_at": issue.created_at
        }
        items.append(IssueItem(**item_dict))
    
    return IssuePage(
        meta=PageMeta(page=page, size=size, total_size=total, total_pages=pages),
        items=items
    )

# ~~~ role and access
def create_role(db: Session, name: str) -> Role:
    if db.query(Role).filter_by(rolename=name).first():
        raise ValueError("Role already exists")
    role = Role(rolename=name)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role

def list_roles(db: Session) -> list[Role]:
    return db.query(Role).order_by(Role.rolename).all()

def grant_access(db: Session, user_id: int, repo_id: int, role_id: int) -> None:
    """Grant a user a specific role on a repo (typically 'developer')."""
    # Check if user is already a developer or owner on this repo
    repo = db.query(Repository).filter_by(repo_id=repo_id).first()
    if not repo:
        raise ValueError("Repository not found")
    if repo.maintainer_id == user_id:
        raise ValueError("User is already the repository owner")
    
    exists = db.query(user_repo_roles).filter_by(
        user_id=user_id, repo_id=repo_id
    ).first()
    if exists:
        raise ValueError("User already has access to this repository")
    
    db.execute(
        user_repo_roles.insert(),
        {"user_id": user_id, "repo_id": repo_id, "role_id": role_id}
    )
    db.commit()

def revoke_access(db: Session, user_id: int, repo_id: int, role_id: int | None = None) -> int:
    """Revoke user access to repo. Returns number of rows deleted (0 = nothing)."""
    stmt = delete(user_repo_roles).where(
        (user_repo_roles.c.user_id == user_id) &
        (user_repo_roles.c.repo_id == repo_id)
    )
    if role_id is not None:
        stmt = stmt.where(user_repo_roles.c.role_id == role_id)
    result = db.execute(stmt)
    db.commit()
    return result.rowcount

def get_repo_members(db: Session, repo_id: int) -> list:
    """Get all users with explicit roles on a repo (excludes owner)."""
    rows = db.query(User, Role).join(
        user_repo_roles, User.user_id == user_repo_roles.c.user_id
    ).join(
        Role, Role.role_id == user_repo_roles.c.role_id
    ).filter(
        user_repo_roles.c.repo_id == repo_id
    ).all()
    
    return [
        {
            "user_id": user.user_id,
            "username": user.username,
            "role": role.rolename
        }
        for user, role in rows
    ]

def get_user_repo_role(db: Session, user_id: int, repo_id: int) -> Optional[str]:
    """Get the role of a user on a specific repo. Returns 'owner', 'developer', 'tester', or None."""
    # Check if user is the maintainer/owner
    repo = db.query(Repository).filter_by(repo_id=repo_id).first()
    if repo and repo.maintainer_id == user_id:
        return "owner"
    
    # Check if user has an explicit role on the repo
    # Join with Role to get the role name directly
    result = db.query(Role).join(
        user_repo_roles, Role.role_id == user_repo_roles.c.role_id
    ).filter(
        user_repo_roles.c.user_id == user_id,
        user_repo_roles.c.repo_id == repo_id
    ).first()
    
    if result:
        return result.rolename
    
    # No explicit role found
    return None

def check_user_repo_access(db: Session, user_id: int, repo_id: int) -> bool:
    """Check if user has ANY role on the repo or is the maintainer."""
    role = get_user_repo_role(db, user_id, repo_id)
    return role is not None

def can_push_repo(db: Session, user_id: int, repo_id: int) -> bool:
    """Check if user has push access (owner or developer role)."""
    role = get_user_repo_role(db, user_id, repo_id)
    return role in ["owner", "developer"]

# ~~~ Fork
def fork_repo(db: Session, source_repo_id: int, new_reponame: str, forker_user_id: int) -> Repository:
    """
    Fork a repository - creates a new repo linked to the original.
    """
    from .git_ops import fork_bare_repo
    
    # Get source repository
    source_repo = db.query(Repository).filter_by(repo_id=source_repo_id).first()
    if not source_repo:
        raise ValueError("Source repository not found")
    
    # Create new repository record
    forked_repo = Repository(
        reponame=new_reponame,
        maintainer_id=forker_user_id,
        fork_of_id=source_repo_id
    )
    
    try:
        # Clone the git repository on disk
        fork_bare_repo(source_repo.reponame, new_reponame)
    except FileExistsError:
        raise ValueError("Repository with that name already exists on disk")
    except Exception as e:
        raise ValueError(f"Failed to fork repository: {str(e)}")
    
    try:
        db.add(forked_repo)
        db.commit()
        db.refresh(forked_repo)
        return forked_repo
    except Exception as e:
        db.rollback()
        # Try to clean up the cloned repo if DB insertion failed
        import shutil
        from .git_ops import REPO_ROOT
        target_path = REPO_ROOT / f"{new_reponame}.git"
        if target_path.exists():
            shutil.rmtree(target_path)
        raise e

# ~~~ Access Log
def log_action(db: Session, repo_id: int, user_id: int, action: Action) -> AccessLog:
    """
    Create an access log entry for a repository action.
    Auto-increments log_no for each repository.
    """
    max_log_no = db.query(func.max(AccessLog.log_no)).filter_by(repo_id=repo_id).scalar() or 0
    next_log_no = max_log_no + 1

    log_entry = AccessLog(
        repo_id=repo_id,
        log_no=next_log_no,
        user_id=user_id,
        action=action
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry

def get_repo_access_logs(db: Session, repo_id: int, page: int = 1, size: int = 20) -> AccessLogPage:
    """
    Get access logs for a specific repository.
    Only repo owners should be able to call this.
    """
    offset = (page - 1) * size
    total = db.query(func.count(AccessLog.log_no)).filter_by(repo_id=repo_id).scalar()

    rows = (db.query(AccessLog, User.username, Repository.reponame)
              .join(User, User.user_id == AccessLog.user_id)
              .join(Repository, Repository.repo_id == AccessLog.repo_id)
              .filter(AccessLog.repo_id == repo_id)
              .order_by(AccessLog.updated_at.desc())
              .offset(offset)
              .limit(size)
              .all())

    pages = ceil(total / size) if total else 1

    return AccessLogPage(
        meta=PageMeta(page=page, size=size, total_size=total, total_pages=pages),
        items=[
            AccessLogItem(
                repo_id=log.repo_id,
                log_no=log.log_no,
                user_id=log.user_id,
                username=username,
                reponame=reponame,
                action=log.action.value,
                created_at=log.updated_at
            )
            for log, username, reponame in rows
        ]
    )

def get_user_access_logs(db: Session, user_id: int, page: int = 1, size: int = 20) -> AccessLogPage:
    """
    Get all access logs for a specific user.
    Users can see their own access logs.
    """
    offset = (page - 1) * size
    total = db.query(func.count(AccessLog.log_no)).filter_by(user_id=user_id).scalar()

    rows = (db.query(AccessLog, User.username, Repository.reponame)
              .join(User, User.user_id == AccessLog.user_id)
              .join(Repository, Repository.repo_id == AccessLog.repo_id)
              .filter(AccessLog.user_id == user_id)
              .order_by(AccessLog.updated_at.desc())
              .offset(offset)
              .limit(size)
              .all())

    pages = ceil(total / size) if total else 1

    return AccessLogPage(
        meta=PageMeta(page=page, size=size, total_size=total, total_pages=pages),
        items=[
            AccessLogItem(
                repo_id=log.repo_id,
                log_no=log.log_no,
                user_id=log.user_id,
                username=username,
                reponame=reponame,
                action=log.action.value,
                created_at=log.updated_at
            )
            for log, username, reponame in rows
        ]
    )