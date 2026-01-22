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

# Fork a bare repo
def fork_bare_repo(source_repo_name: str, new_repo_name: str) -> Path:
    """
    Fork/clone a bare repository to a new bare repository.
    Uses git clone --bare to create a complete copy.
    """
    source_path = get_repo_path(source_repo_name)
    target_path = REPO_ROOT / f"{new_repo_name}.git"
    
    if target_path.exists():
        raise FileExistsError("Target repository already exists")
    
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Clone the bare repository
    try:
        result = subprocess.run(
            ["git", "clone", "--bare", str(source_path), str(target_path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            raise Exception(f"Git clone failed: {result.stderr}")
        
        return target_path.resolve()
    except Exception as e:
        # Clean up if fork failed
        if target_path.exists():
            import shutil
            shutil.rmtree(target_path)
        raise

# List files in repo
def list_repo_files(repo_name: str) -> list[dict]:
    """
    List all files in the repository using git ls-tree.
    Returns a list of dicts with file info: name, type, path
    """
    try:
        repo_path = get_repo_path(repo_name)
        
        # Get the HEAD ref to list files
        result = subprocess.run(
            ["git", "ls-tree", "-r", "HEAD"],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            # Repository might be empty
            if "fatal: Not a valid object name" in result.stderr:
                return []
            raise Exception(f"Git error: {result.stderr}")
        
        files = []
        for line in result.stdout.strip().split('\n'):
            if not line.strip():
                continue
            
            # Format: <mode> SP <type> SP <object> SP <size> TAB <file>
            parts = line.split('\t')
            if len(parts) != 2:
                continue
            
            file_path = parts[1]
            file_info = parts[0].split()
            
            if len(file_info) >= 2:
                file_type = file_info[1]  # "blob" or "tree"
                files.append({
                    "name": file_path.split('/')[-1],
                    "path": file_path,
                    "type": file_type
                })
        
        return sorted(files, key=lambda x: (x['type'] != 'tree', x['name']))  # Dirs first
    
    except Exception as e:
        print(f"Error listing files: {e}")
        return []