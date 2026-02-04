import os
import logging
import subprocess
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func
from starlette.responses import StreamingResponse

from . import models, json_dto, crud, git_ops, auth
from .crud import get_issue_thread
from .dependency_injector import get_db
from .database_sessions import engine
from .git_ops import get_repo_path
from .json_dto import RepoCreate, IssueCreate, CommentCreate, IssueDetailResponse, IssuePage, RepoPage, RoleCreate, RoleResponse, AccessGrant, AccessRevoke, UserPage, UserItem, UserTierUpdate, UserResponse, RepoFilesResponse, ForkCreate, ForkResponse, AccessLogPage
from .models import Role, UserTier, User, Action
from .auth import require_admin, require_dev_up

app = FastAPI(title="Private Repo Manager")

# Add CORS middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for serving the frontend
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="frontend")

models.Base.metadata.create_all(bind=engine)
logger = logging.getLogger(__name__)

# Serve index.html at root path
@app.get("/", include_in_schema=False)
async def serve_frontend():
    from fastapi.responses import FileResponse
    frontend_path = Path(__file__).parent.parent / "frontend" / "index.html"
    return FileResponse(frontend_path)
logger = logging.getLogger(__name__)

# repo endpoints
# making new repository
@app.post("/repos", response_model=json_dto.RepoResponse, dependencies=[Depends(require_dev_up)],tags=["repos"])
def init_repo(payload: RepoCreate, 
              db: Session = Depends(get_db),
              current_user: models.User = Depends(auth.get_current_user)):
    try:
        # Override maintainer_id with current user to prevent spoofing
        payload.maintainer_id = current_user.user_id
        return crud.create_repo(db=db, repo_in=payload)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.exception("An unhandled error occurred while creating a repo")
        raise HTTPException(status_code=500, detail="Internal server error")

# get all repos
@app.get("/repos", response_model=RepoPage, tags=["repos"])
def read_repos(page: int = Query(1, ge=1),
               size: int = Query(20, ge=1, le=100),
               db: Session = Depends(get_db)):
    return crud.list_repos(db, page, size)

# delete a repository
@app.delete("/repos/{repo_id}", dependencies=[Depends(require_dev_up)], tags=["repos"])
def delete_repository(repo_id: int,
                     db: Session = Depends(get_db),
                     current_user: models.User = Depends(auth.get_current_user)):
    try:
        repo = db.query(models.Repository).filter_by(repo_id=repo_id).one()
    except:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # Only maintainer or admin can delete
    if repo.maintainer_id != current_user.user_id and current_user.tier != models.UserTier.admin:
        raise HTTPException(status_code=403, detail="Only repository owner or admin can delete")
    
    # Log delete action before deletion
    try:
        crud.log_action(db, repo_id, current_user.user_id, Action.DELETE)
    except Exception as e:
        logger.error(f"Failed to log delete action: {e}")
    
    # Delete the git repository from filesystem
    try:
        repo_path = get_repo_path(repo.reponame)
        if repo_path.exists():
            import shutil
            shutil.rmtree(repo_path)
    except Exception as e:
        logger.error(f"Failed to delete repo directory: {e}")
    
    db.delete(repo)
    db.commit()
    return {"message": "Repository deleted successfully"}

# get files in a repo
@app.get("/repos/{repo_id}/files", response_model=RepoFilesResponse, tags=["repos"])
def get_repo_files(repo_id: int,
                   db: Session = Depends(get_db)):
    repo = crud.get_repo_by_id(db, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    files = git_ops.list_repo_files(repo.reponame)
    return RepoFilesResponse(
        repo_id=repo_id,
        reponame=repo.reponame,
        files=[json_dto.RepoFile(**f) for f in files]
    )

# fork a repository
@app.post("/repos/{repo_id}/fork", response_model=ForkResponse, dependencies=[Depends(require_dev_up)], tags=["repos"])
def fork_repository(repo_id: int,
                   payload: ForkCreate,
                   db: Session = Depends(get_db),
                   current_user: models.User = Depends(auth.get_current_user)):
    """
    Fork a repository - creates a new repository that is a copy of the original.
    """
    try:
        forked = crud.fork_repo(db, repo_id, payload.new_reponame, current_user.user_id)
        
        # Log fork action
        try:
            crud.log_action(db, repo_id, current_user.user_id, Action.FORK)
        except Exception as e:
            logger.exception(f"Failed to log fork action: {e}")
        
        return forked
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("An unhandled error occurred while forking a repo")
        raise HTTPException(status_code=500, detail="Internal server error")

# Issues Endpoints
# making new issue
@app.post("/repos/{repo_id}/issues", response_model=json_dto.IssueResponse, tags=["repos"])
def new_issue(repo_id: int,
              payload: IssueCreate,
              current_user: models.User = Depends(auth.get_current_user),
              db: Session = Depends(get_db)):
    return crud.create_issue(db=db, repo_id=repo_id, author_id=current_user.user_id, issue_in=payload)

# adding a comment to issue
@app.post("/repos/{repo_id}/issues/{issue_num}/comments", tags=["repos"])
def add_comment(repo_id: int,
                issue_num: int,
                payload: CommentCreate,
                current_user: models.User = Depends(auth.get_current_user),
                db: Session = Depends(get_db)):
    crud.append_comment(db, repo_id, issue_num, current_user.user_id, payload.body)
    return {"reply": "comment added"}

# opening and viewing an issue thread
@app.get("/repos/{repo_id}/issues/{issue_num}", response_model=IssueDetailResponse, tags=["repos"])
def read_issue(repo_id: int,
               issue_num: int,
               db: Session = Depends(get_db),
               current_user: models.User = Depends(auth.get_current_user)):
    return get_issue_thread(db, repo_id, issue_num)
# view all issue
@app.get("/repos/{repo_id}/issues", response_model=IssuePage, tags=["repos"])
def read_issues(repo_id: int,
                page: int = Query(1, ge=1),
                size: int = Query(20, ge=1, le=100),
                db: Session = Depends(get_db),
                current_user: models.User = Depends(auth.get_current_user)):
    return crud.list_issues(db, repo_id, page, size)

# close/reopen issue
@app.patch("/repos/{repo_id}/issues/{issue_num}/status", tags=["repos"])
def update_issue_status(repo_id: int,
                       issue_num: int,
                       status: str,
                       db: Session = Depends(get_db),
                       current_user: models.User = Depends(auth.get_current_user)):
    try:
        issue = db.query(models.Issue).filter_by(repo_id=repo_id, issue_num=issue_num).one()
    except:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    # Only author or admin/developer can close issues
    if issue.author_id != current_user.user_id and current_user.tier not in [models.UserTier.admin, models.UserTier.developer]:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    if status == "closed":
        issue.status = models.IssueStatus.CLOSED
    elif status == "open":
        issue.status = models.IssueStatus.OPEN
    else:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    issue.updated_at = func.now()
    db.commit()
    db.refresh(issue)
    return {"status": issue.status.value}


# User endpoints
# making new users
@app.post("/users", response_model=json_dto.UserResponse, tags=["users"])
def create_user(user: json_dto.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_name(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username exists")
    return crud.create_user(db, user)

# Authentication endpoint - verify current user
@app.get("/auth/me", response_model=UserResponse, tags=["auth"])
def get_current_user_info(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

@app.get("/user/my-repos", tags=["repos"])
def get_user_repos(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Get all repos the user has access to (owned, developer, or tester), with their role."""
    all_repos = db.query(models.Repository).all()
    
    user_repos = []
    for repo in all_repos:
        # Check user's role in this repo
        role = crud.get_user_repo_role(db, current_user.user_id, repo.repo_id)
        
        # If user is owner, role is None but we treat them as owner
        if repo.maintainer_id == current_user.user_id:
            role = "owner"
        elif role is None:
            # User has no explicit role, default to tester
            role = "tester"
        
        user_repos.append({
            "repo_id": repo.repo_id,
            "reponame": repo.reponame,
            "maintainer_id": repo.maintainer_id,
            "maintainer_name": repo.maintainer.username if repo.maintainer else "unknown",
            "role": role
        })
    
    return {"repos": user_repos}

@app.get("/users", response_model=UserPage, tags=["users"])
def get_users(page: int = Query(1, ge=1),
              size: int = Query(20, ge=1, le=100),
              db: Session = Depends(get_db),
              current_user: models.User = Depends(require_admin)):  # only admins
    return crud.list_users(db, page, size)

@app.patch("/users/{user_id}/tier", response_model=UserResponse, tags=["users"])
def update_user_tier(
    user_id: int,
    payload: UserTierUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)   # only admins
):
    try:
        updated = crud.change_user_tier(db, user_id, UserTier(payload.tier))
    except ValueError as e:
        raise HTTPException(404, detail=str(e))
    return updated

# GIT ENDPOINTS ~~~
@app.get("/{repo_name:path}.git/info/refs", tags=["git"])
async def git_info_refs(repo_name: str, service: str, 
                        user: models.User = Depends(auth.verify_git_access)):
    """
    Step 1 : Handle info/refs for both clone and push operations.

    This endpoint advertises what refs (branches, tags) are available.
    - For clone: service=git-upload-pack
    - For push: service=git-receive-pack
    """

    print(f"DEBUG: Received info/refs request for repo: {repo_name}, service: {service}")

    # Get repo from database to log the action
    from .dependency_injector import get_db as _get_db
    db = next(_get_db())
    repo = crud.get_repo_by_name(db, repo_name)
    
    # Log clone or pull action (upload-pack = clone/pull)
    if repo and service == "git-upload-pack":
        try:
            crud.log_action(db, repo.repo_id, user.user_id, Action.CLONE)
        except Exception as e:
            logger.error(f"Failed to log clone action: {e}")
    
    # Validate service parameter
    if service not in ["git-upload-pack", "git-receive-pack"]:
        raise HTTPException(status_code=400, detail="Invalid service")
    git_command = service.replace("git-", "")
    try:
        repo_path = get_repo_path(repo_name)
        print(f"DEBUG: Repository path: {repo_path}")
        print(f"DEBUG: Path exists: {repo_path.exists()}")
    except HTTPException as e:
        print(f"DEBUG: Repository not found: {e.detail}")
        raise

    # Execute git command to advertise refs
    try:
        cmd = ["git", git_command, "--stateless-rpc", "--advertise-refs", str(repo_path)]
        print(f"DEBUG: Executing command: {' '.join(cmd)}")

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(repo_path)  # Execute in repo directory
        )

        output, error = process.communicate(timeout=10)  # Add timeout

        print(f"DEBUG: Git command return code: {process.returncode}")
        print(f"DEBUG: Git stdout length: {len(output)} bytes")
        print(f"DEBUG: Git stdout (first 200 chars): {output[:200]}")
        if error:
            print(f"DEBUG: Git stderr: {error.decode()}")

        if process.returncode != 0:
            error_msg = error.decode() if error else "Unknown error"
            print(f"ERROR: Git command failed with code {process.returncode}: {error_msg}")
            raise HTTPException(
                status_code=500,
                detail=f"Git command failed: {error_msg}"
            )

        # Build response in Git packet-line format
        service_announcement = git_ops.packet_line(f"# service={service}\n")
        flush = b"0000"
        response_body = service_announcement + flush + output

        print(f"DEBUG: Response body length: {len(response_body)} bytes")
        print(f"DEBUG: Response body (first 100 chars): {response_body[:100]}")

        # Set appropriate content-type
        content_type = f"application/x-{service}-advertisement"
        print(f"DEBUG: Content-Type: {content_type}")

        return Response(
            content=response_body,
            media_type=content_type,
            headers={
                "Cache-Control": "no-cache",
                "Expires": "Fri, 01 Jan 1980 00:00:00 GMT",
                "Pragma": "no-cache"
            }
        )

    except subprocess.SubprocessError as e:
        print(f"DEBUG: Subprocess error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Subprocess error: {str(e)}")
    except Exception as e:
        print(f"DEBUG: Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@app.post("/{repo_name:path}.git/git-upload-pack", tags=["git"])
async def git_upload_pack(repo_name: str, request: Request,
                          user: models.User = Depends(auth.verify_git_access)):
    """
    This is to handle git-upload-pack (clone/fetch operations).

    This is where the actual packfile transfer happens for clone.
    Client sends what it wants, we send back the Git objects.
    """
    repo_path = get_repo_path(repo_name)
    # Read the request body (client's want/have negotiation)
    request_body = await request.body()
    try:
        # Start git upload-pack process
        process = subprocess.Popen(
            ["git", "upload-pack", "--stateless-rpc", str(repo_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        # Stream the response
        return StreamingResponse(
            git_ops.stream_git_process(process, request_body),
            media_type="application/x-git-upload-pack-result",
            headers={
                "Cache-Control": "no-cache",
                "Expires": "Fri, 01 Jan 1980 00:00:00 GMT",
                "Pragma": "no-cache"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload pack failed: {str(e)}")


@app.post("/{repo_name}.git/git-receive-pack", tags=["git"])
async def git_receive_pack(repo_name: str, request: Request,
                           user: models.User = Depends(auth.verify_git_access)):
    """
    this is to handle git-receive-pack (push operations).

    This is where the actual packfile transfer happens for push.
    Client sends new commits/objects, we update the repository.
    """
    # Get repo from database to check permissions and log the action
    from .dependency_injector import get_db as _get_db
    db = next(_get_db())
    repo = crud.get_repo_by_name(db, repo_name)
    
    # Check push access: only owner and developer roles can push
    if repo and not crud.can_push_repo(db, user.user_id, repo.repo_id):
        raise HTTPException(
            status_code=403, 
            detail="Push access denied. Only repository owner and developers can push."
        )
    
    # Log push action
    if repo:
        try:
            crud.log_action(db, repo.repo_id, user.user_id, Action.PUSH)
        except Exception as e:
            logger.error(f"Failed to log push action: {e}")
    
    repo_path = get_repo_path(repo_name)
    # Read the request body (packfile + ref updates)
    request_body = await request.body()
    try:
        # Start git receive-pack process
        process = subprocess.Popen(
            ["git", "receive-pack", "--stateless-rpc", str(repo_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        # Stream the response
        return StreamingResponse(
            git_ops.stream_git_process(process, request_body),
            media_type="application/x-git-receive-pack-result",
            headers={
                "Cache-Control": "no-cache",
                "Expires": "Fri, 01 Jan 1980 00:00:00 GMT",
                "Pragma": "no-cache"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Receive pack failed: {str(e)}")


# ROLE endpoints
@app.post("/roles", response_model=RoleResponse, dependencies=[Depends(require_admin)],status_code=201, tags=["roles"])
def new_role(payload: RoleCreate, db: Session = Depends(get_db)):
    try:
        role = crud.create_role(db, payload.rolename)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return role

@app.get("/roles", response_model=list[RoleResponse], tags=["roles"])
def get_roles(db: Session = Depends(get_db)):
    return crud.list_roles(db)

@app.post("/access", status_code=201, tags=["roles"])
def grant_access_endpoint(payload: AccessGrant, 
                          db: Session = Depends(get_db),
                          current_user: models.User = Depends(auth.get_current_user)):
    repo = crud.get_repo_by_id(db, payload.repo_id)
    if not repo:
        raise HTTPException(404, detail="Repository not found")
    
    # Debug logging
    logger.info(f"Grant access attempt: repo_id={payload.repo_id}, maintainer_id={repo.maintainer_id}, current_user_id={current_user.user_id}, current_user_tier={current_user.tier}")
    
    # Allow repo owner or admin to grant access
    is_owner = repo.maintainer_id == current_user.user_id
    is_admin = current_user.tier == models.UserTier.admin
    
    if not (is_owner or is_admin):
        raise HTTPException(403, detail="Only the repository owner or admin can grant access")
        
    try:
        crud.grant_access(db, payload.user_id, payload.repo_id, payload.role_id)
    except ValueError as e:
        raise HTTPException(409, detail=str(e))
    return {"msg": "access granted"}

@app.delete("/access", tags=["roles"])
def revoke_access_endpoint(payload: AccessRevoke,
                           role_id: int | None = Query(None, description="Optional: remove only this role"),
                           db: Session = Depends(get_db),
                           current_user: models.User = Depends(auth.get_current_user)):
    repo = crud.get_repo_by_id(db, payload.repo_id)
    if not repo:
        raise HTTPException(404, detail="Repository not found")
    
    # Allow repo owner or admin to revoke access
    is_owner = repo.maintainer_id == current_user.user_id
    is_admin = current_user.tier == models.UserTier.admin
    
    if not (is_owner or is_admin):
        raise HTTPException(403, detail="Only the repository owner or admin can revoke access")
        
    deleted = crud.revoke_access(db, payload.user_id, payload.repo_id, role_id)
    if deleted == 0:
        raise HTTPException(404, detail="Access relationship not found")
    return {"msg": f"{deleted} access row(s) removed"}

@app.get("/repos/{repo_id}/members", tags=["repos"])
def get_repo_members(repo_id: int,
                     db: Session = Depends(get_db)):
    """Get all members (developers) of a repository."""
    repo = crud.get_repo_by_id(db, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    members = crud.get_repo_members(db, repo_id)
    return {
        "repo_id": repo_id,
        "repo_name": repo.reponame,
        "owner_id": repo.maintainer_id,
        "members": members
    }

@app.get("/repos/{repo_id}/available-users", tags=["repos"])
def get_available_users_for_repo(repo_id: int,
                                  db: Session = Depends(get_db),
                                  current_user: models.User = Depends(auth.get_current_user)):
    """Get list of users that can be added as developers to a repository."""
    repo = crud.get_repo_by_id(db, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # Only owner or admin can see this list
    is_owner = repo.maintainer_id == current_user.user_id
    is_admin = current_user.tier == models.UserTier.admin
    
    if not (is_owner or is_admin):
        raise HTTPException(403, detail="Only the repository owner or admin can view available users")
    
    # Get all users
    all_users = db.query(User).all()
    
    # Get current members
    current_members = crud.get_repo_members(db, repo_id)
    member_ids = {m['user_id'] for m in current_members}
    member_ids.add(repo.maintainer_id)  # Add owner to exclusion list
    
    # Filter out owner and existing members
    available_users = [
        {"user_id": user.user_id, "username": user.username, "email": user.email}
        for user in all_users
        if user.user_id not in member_ids
    ]
    
    return {"users": available_users}

@app.get("/health")
def health_check():
    return {"status": str(get_repo_path("repo1"))}

# ACCESS LOG endpoints
@app.get("/repos/{repo_id}/logs", response_model=AccessLogPage, tags=["logs"])
def get_repository_logs(
    repo_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Get access logs for a repository.
    Only the repository owner can view logs.
    """
    repo = crud.get_repo_by_id(db, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # Only repo owner can view logs
    if repo.maintainer_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Only repository owner can view access logs")
    
    return crud.get_repo_access_logs(db, repo_id, page, size)

@app.get("/users/me/logs", response_model=AccessLogPage, tags=["logs"])
def get_my_logs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Get access logs for the current user.
    Users can see all their own access logs across all repositories.
    """
    return crud.get_user_access_logs(db, current_user.user_id, page, size)

def seed_roles(db: Session):
    defaults = ["admin", "developer", "tester"]
    for name in defaults:
        if not db.query(Role).filter_by(rolename=name).first():
            db.add(Role(rolename=name))
    db.commit()

    root = db.query(User).filter_by(username="root").first()
    if not root:
        db.add(User(username="root",
                    email="root@local",
                    password_hash=crud.hash_pwd("admin123"),
                    tier=UserTier.admin))
    else:
         # Ensure root is always admin
         if root.tier != UserTier.admin:
             root.tier = UserTier.admin
             db.add(root)
    db.commit()
seed_roles(next(get_db()))