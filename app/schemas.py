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
