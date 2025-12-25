import os
import logging
import subprocess
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

from . import models, json_dto, crud, git_ops
from .crud import get_issue_thread
from .dependency_injector import get_db, fake_current_user
from .database_sessions import engine
from .git_ops import get_repo_path

from .json_dto import RepoCreate, IssueCreate, CommentCreate, IssueDetailResponse, IssuePage, RepoPage

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

# get all repos
@app.get("/repos", response_model=RepoPage, tags=["repos"])
def read_repos(page: int = Query(1, ge=1),
               size: int = Query(20, ge=1, le=100),
               db: Session = Depends(get_db)):
    return crud.list_repos(db, page, size)

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

# GIT ENDPOINTS ~~~
@app.get("/{repo_name:path}.git/info/refs")
async def git_info_refs(repo_name: str, service: str):
    """
    Step 1 : Handle info/refs for both clone and push operations.

    This endpoint advertises what refs (branches, tags) are available.
    - For clone: service=git-upload-pack
    - For push: service=git-receive-pack
    """

    print(f"DEBUG: Received info/refs request for repo: {repo_name}, service: {service}")

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


@app.post("/{repo_name:path}.git/git-upload-pack")
async def git_upload_pack(repo_name: str, request: Request):
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


@app.post("/{repo_name}.git/git-receive-pack")
async def git_receive_pack(repo_name: str, request: Request):
    """
    this is to handle git-receive-pack (push operations).

    This is where the actual packfile transfer happens for push.
    Client sends new commits/objects, we update the repository.
    """
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

@app.get("/health")
def health_check():
    return {"status": str(get_repo_path("repo1"))}