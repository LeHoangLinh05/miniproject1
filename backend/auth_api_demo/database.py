from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings

# Default to SQLite local database if DATABASE_URL is not set
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# SQLite requires check_same_thread: False, but PostgreSQL doesn't support it
is_sqlite = SQLALCHEMY_DATABASE_URL.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}

engine_kwargs: dict[str, object] = {"connect_args": connect_args}
if not is_sqlite:
    engine_kwargs["pool_pre_ping"] = True

engine = create_engine(SQLALCHEMY_DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """
    SQLAlchemy DeclarativeBase class for 2.0 style declarative models.
    """

    pass


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency to provide a database session for each request.
    Ensures the connection is closed after the request is finished.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
