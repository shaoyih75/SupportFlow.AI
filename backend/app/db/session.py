from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# expire_on_commit=False: objects stay readable after commit, so services can
# build the Pydantic response without an extra SELECT.
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session() -> Iterator[Session]:
    """FastAPI dependency: one Session per request, always closed afterwards."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@contextmanager
def transaction(session: Session) -> Iterator[Session]:
    """Transaction boundary used by Services (not Routes, not Repositories).

    Commits if the block finishes, rolls back everything if it raises.
    Same idea as `with session.begin():`, but also works when an earlier read in the
    same request (e.g. loading the current user) has already started a transaction.
    """
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
