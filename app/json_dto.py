# pydantic schemas / dtos
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RepoCreate(BaseModel):
    reponame: str
    maintainer_id : int

class RepoResponse(BaseModel):
    repo_id: int
    reponame: str
    maintainer_id : int
    class Config:
        from_attributes=True

class RepoItem(BaseModel):
    repo_id: int
    reponame: str
    maintainer_name: str
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

# to see issue and its comment thread
class IssueDetailResponse(BaseModel):
    repo_id: int
    issue_num: int
    title: str
    author_id: int
    body: str
    created_at: datetime
    comments: list[CommentItem]

# issue page
class PageMeta(BaseModel):
    page: int
    size: int
    total_size: int
    total_pages: int

# issue details in the page that shows all issues
class IssueItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    issue_num: int
    title: str
    author_id: int
    status: str
    created_at: datetime
# issue page
class IssuePage(BaseModel):
    meta: PageMeta
    items: list[IssueItem]

class RepoPage(BaseModel):
    meta: PageMeta
    items: list[RepoItem]