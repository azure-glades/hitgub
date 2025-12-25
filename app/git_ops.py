import subprocess
import asyncio
from pathlib import Path
from typing import AsyncGenerator, AsyncIterator

from fastapi import HTTPException
from git import Repo
import os

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR / "tmp" / "repos"

# ~~~ helper
def get_repo_path(repo_name: str) -> Path:
    """Get the filesystem path for a repository"""
    repo_path = REPO_ROOT / f"{repo_name}.git"
    if not repo_path.exists():
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo_path

def packet_line(data: str) -> bytes:
    """
    Create a Git packet-line format string.
    Format: 4-byte hex length (including the 4 bytes) + data
    """
    if data:
        # +4 for the length prefix itself
        size = len(data) + 4
        return f"{size:04x}".encode() + data.encode()
    return b"0000"  # flush packet

# git init a bare repo
def init_bare(repo_name: str) -> Path:
    repo_path = REPO_ROOT / f"{repo_name}.git"
    repo_path.parent.mkdir(parents=True, exist_ok=True)
    if repo_path.exists():
        raise FileExistsError("Bare repo already exists")
    Repo.init(repo_path, bare=True)
    return repo_path.resolve()

# git stuff
async def stream_git_process(
        process: subprocess.Popen,
        request_body: bytes = None
) -> AsyncIterator[bytes]:
    """
    Stream data through a Git subprocess.
    Optionally sends request_body to stdin, then yields stdout.
    """
    try:
        # If we have request body, write it to git's stdin
        if request_body:
            process.stdin.write(request_body)
            process.stdin.close()

        # Stream the output back
        while True:
            chunk = process.stdout.read(8192)
            if not chunk:
                break
            yield chunk

        # Wait for process to complete
        process.wait()

        # Check for errors
        if process.returncode != 0:
            stderr_output = process.stderr.read()
            print(f"Git process error: {stderr_output.decode()}")

    except Exception as e:
        print(f"Error streaming git process: {e}")
        if process.poll() is None:
            process.kill()
        raise
    finally:
        if process.stdout:
            process.stdout.close()
        if process.stderr:
            process.stderr.close()
            process.stderr.close()