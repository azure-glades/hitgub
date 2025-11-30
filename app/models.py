# tables are defined as objects here

from sqlalchemy import Table, Column, Integer, String, Boolean, DateTime, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, declarative_base, func
from datetime import datetime
import enum
Base = declarative_base()

# enum
class Action(enum.Enum):
    CLONE   = "clone"
    PUSH    = "push"
    PULL    = "pull"
    FORK    = "fork"
    DELETE  = "delete"

# ternary relationship "access"
user_repo_roles = Table(
    'user_repo_roles',
    Base.metadata,
    Column('user_id', ForeignKey('user.user_id'), primary_key=True),
    Column('repo_id', ForeignKey('repository.repo_id'), primary_key=True),
    Column('role_id', ForeignKey('role.role_id'), primary_key=True)
)

# entities
class User(Base):
    __tablename__ = "user"
    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)

    # relationships
    maintained_repos = relationship(
        "Repository",
        back_populates="maintainer",
        foreign_keys="Repository.maintainer_id"
    )
    authored_issues = relationship(
        "Issue",
        back_populates="author",
        foreign_keys="Issue.author_id"
    )
    assigned_issues = relationship(
        "Issue",
        back_populates="assignee",
        foreign_keys="Issue.assignee_id"
    )

class Repository(Base):
    __tablename__ = "repository"
    repo_id = Column(Integer, primary_key=True, index=True)
    reponame = Column(String, index=True, nullable=False)
    maintainer_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    fork_of_id = Column(Integer, ForeignKey("repository.repo_id"), nullable=True)

    # relationship
    maintainer = relationship(
        "User",
        back_populates="maintained_repos",   # other side must use this name
        foreign_keys=[maintainer_id]
    )
    has_issue = relationship(
        "Issue",
        back_populates="issue_of",
        foreign_keys="Issue.repo_id",
        cascade="all, delete-orphan"
    )
    has_log = relationship(
        "AccessLog",
        back_populates="log_of",
        foreign_keys="AccessLog.repo_id",
        cascade="all, delete-orphan"
    )
    # recursive rel
    fork_of = relationship(
        "Repository",
        remote_side=[repo_id],
        backref="forks",
    )

    # constraints
    __table_args__ = (
        UniqueConstraint("reponame", "maintainer_id"),
    )

class Role(Base):
    __tablename__ = "role"
    role_id = Column(Integer, primary_key=True, index=True)
    rolename = Column(String, unique=True, index=True)

class Issue(Base):
    __tablename__ = "issue"
    repo_id = Column(Integer, ForeignKey("repository.repo_id"), primary_key=True, index=True)
    issue_num = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer, ForeignKey("user.user_id"), nullable=False, index=True)
    
    assignee_id = Column(Integer, ForeignKey("user.user_id"))
    title = Column(String)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    nosql_thread_id = Column(String)  # mongoDB object id

    # relationships
    author = relationship(
        "User",
        back_populates="authored_issues",
        foreign_keys=[author_id]
    )
    assignee = relationship(
        "User",
        back_populates="assigned_issues",
        foreign_keys=[assignee_id]
    )
    issue_of = relationship(
        "Repository",
        back_populates="has_issue",
        foreign_keys=[repo_id]
    )

    __table_args__ = (
        UniqueConstraint("repo_id", "issue_num") # uniquesness
    )

class AccessLog(Base):
    __tablename__ = "accesslog"
    repo_id = Column(Integer, ForeignKey("repository.repo_id"), primary_key=True, index=True)
    log_no = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.user_id"), primary_key=True, index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    action = Column(Enum(Action), nullable=False, index=True)

    # relationships
    log_of = relationship(
        "Repository",
        back_populates="has_log",
        foreign_keys=[repo_id]
    )

    __table_args__ = (
        UniqueConstraint("repo_id", "log_no") # uniquesness
    )