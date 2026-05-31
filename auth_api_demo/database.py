import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Default to PostgreSQL, fallback to SQLite if DATABASE_URL is not set
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL"
    # "postgresql://postgres:postgres@localhost:5432/auth_demo"
)

# SQLite requires check_same_thread: False, but PostgreSQL doesn't support it
is_sqlite = SQLALCHEMY_DATABASE_URL.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args=connect_args
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """
    FastAPI dependency to provide a database session for each request.
    Ensures the connection is closed after the request is finished.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
