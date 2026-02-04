# pydantic schemas / dtos
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# basic dto
class PageMeta(BaseModel):
    page: int
    size: int
    total_size: int
    total_pages: int

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
    maintainer_id: int

class RepoFile(BaseModel):
    name: str
    path: str
    type: str  # "blob" or "tree"

class RepoFilesResponse(BaseModel):
    repo_id: int
    reponame: str
    files: list[RepoFile]
# ~~~
class UserCreate(BaseModel):
    username : str
    email: str
    password: str

class UserResponse(BaseModel):
    user_id : int
    username: str
    email: str
    tier: str

    class Config:
        from_attributes=True

class UserItem(BaseModel):
    user_id: int
    username: str
    email: str
    tier: str 

class UserPage(BaseModel):
    meta: PageMeta
    items: list[UserItem]

class UserTierUpdate(BaseModel):
    tier: str = Field(pattern="^(admin|developer|tester)$")

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
    author: str
    body: str
    status: str
    created_at: datetime
    comments: list[CommentItem]

# issue page
# issue details in the page that shows all issues
class IssueItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    issue_num: int
    title: str
    author_id: int
    author: str = ""
    status: str
    created_at: datetime
# issue page
class IssuePage(BaseModel):
    meta: PageMeta
    items: list[IssueItem]

class RepoPage(BaseModel):
    meta: PageMeta
    items: list[RepoItem]


# ~~~ Role
class RoleCreate(BaseModel):
    rolename: str = Field(min_length=1, max_length=50)

class RoleResponse(BaseModel):
    model_config= ConfigDict(from_attributes=True)
    role_id: int
    rolename: str

# ~~~ role-repo-user i.e access
class AccessGrant(BaseModel):
    user_id: int
    repo_id: int
    role_id: int

class AccessRevoke(BaseModel):
    user_id: int
    repo_id: int

# ~~~ Fork
class ForkCreate(BaseModel):
    new_reponame: str

class ForkResponse(BaseModel):
    repo_id: int
    reponame: str
    maintainer_id: int
    fork_of_id: int
    class Config:
        from_attributes=True

# ~~~ Access Log
class AccessLogItem(BaseModel):
    repo_id: int
    log_no: int
    user_id: int
    username: str
    reponame: str
    action: str
    created_at: datetime

class AccessLogPage(BaseModel):
    meta: PageMeta
    items: list[AccessLogItem]