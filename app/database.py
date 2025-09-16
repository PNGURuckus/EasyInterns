from typing import Optional
from sqlmodel import Session, create_engine

# Lightweight database dependency shim for tests and simple usage.
# Tests override this dependency to inject an in-memory session.

_engine = None


def _get_engine():
    global _engine
    if _engine is None:
        # Lazy import to avoid circulars
        from .config import settings
        _engine = create_engine(settings.database_url)
    return _engine


def get_session() -> Session:
    """Return a SQLModel Session. In tests, this is overridden via FastAPI's dependency_overrides."""
    return Session(_get_engine())


def get_engine():
    """Expose the underlying engine for migrations/table creation."""
    return _get_engine()
