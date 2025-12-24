# pydantic schemas / dtos
from datetime import datetime

from pydantic import BaseModel

class RepoCreate(BaseModel):
    reponame: str
    maintainer_id : int

class RepoResponse(BaseModel):
    repo_id: int
    reponame: str
    maintainer_id : int
    class Config:
        from_attributes=True

# ~~~
class UserCreate(BaseModel):
    username : str
    email: str
    password: str

class UserResponse(BaseModel):
    user_id : int
    username: str
    email: str

    class Config:
        from_attributes=True

# ~~~
class IssueCreate(BaseModel):
    title: str
    body: str

class IssueResponse(BaseModel):
    repo_id: int
    issue_num: int
    title: str
    author_id: int
    created_at: datetime
    nosql_thread_id: str # this is an issue thread
    class Config:
        from_attributes=True

class CommentCreate(BaseModel):
    body: str

class CommentItem(BaseModel):
    user: str
    body: str
    timestamp: datetime

class IssueDetailResponse(BaseModel):
    repo_id: int
    issue_num: int
    title: str
    author_id: int
    created_at: datetime
    comments: list[CommentItem]