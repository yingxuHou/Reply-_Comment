import os
from contextlib import contextmanager

from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings


def _sqlite_connect_args(database_url: str) -> dict:
    if database_url.startswith("sqlite:///"):
        return {"check_same_thread": False}
    return {}


engine = create_engine(settings.database_url, connect_args=_sqlite_connect_args(settings.database_url))


def create_db_and_tables() -> None:
    from app import models as _models

    database_url = settings.database_url
    if database_url.startswith("sqlite:///./"):
        db_path = database_url.replace("sqlite:///./", "", 1)
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    SQLModel.metadata.create_all(engine)


@contextmanager
def session_scope():
    with Session(engine) as session:
        yield session


def get_session():
    with Session(engine) as session:
        yield session

