"""
Database connection: engine factory and session context manager.
"""
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from tfais.config.settings import DATABASE_URL
from tfais.database.models import Base

_engine = None
_SessionLocal = None


def get_engine():
    """Return (or lazily create) the SQLAlchemy engine."""
    global _engine
    if _engine is None:
        _engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,       # detect stale connections
            pool_size=5,
            max_overflow=10,
        )
    return _engine


def get_session_factory():
    """Return (or lazily create) the session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _SessionLocal


@contextmanager
def get_session() -> Session:
    """
    Provide a transactional scope around a series of operations.

    Usage:
        with get_session() as session:
            session.add(obj)
    """
    factory = get_session_factory()
    session: Session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_all_tables():
    """Create all tables defined in models.py (idempotent)."""
    Base.metadata.create_all(bind=get_engine())


def drop_all_tables():
    """Drop all tables — for testing only."""
    Base.metadata.drop_all(bind=get_engine())
