from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

POSTGRES_URL = "postgresql+psycopg2://devuser:password@localhost:5432/devdb"

engine = create_engine(POSTGRES_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)