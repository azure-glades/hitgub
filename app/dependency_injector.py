# database url, other dependencies go here
from typing import Generator
from sqlalchemy.orm import Session
from .database_sessions import SessionLocal   # the sessionmaker you already have

def get_db() -> Generator[Session, None, None]:
    """Provide a transactional database session per request."""
    db = SessionLocal()              # opens a connection from the pool
    try:
        yield db                     # injected into path-operators
    finally:
        db.close()                   # always returned to pool

# async get_current_user()
