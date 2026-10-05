"""Shared test configuration.

The application binds SQLAlchemy to ``sqlite:///./devops_maturity.db`` at
import time.  Re-point the shared engine and session factory at a private
in-memory database *before* any test module imports the CLI or the web app,
so the suite never touches a developer's local database and every run starts
from an empty schema.
"""

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from core import model

_test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
model.engine = _test_engine
model.SessionLocal.configure(bind=_test_engine)
model.init_db()
