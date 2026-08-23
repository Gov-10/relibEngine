import os

from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import sessionmaker


DEFAULT_SERVER_URL = (
    "postgresql+psycopg2://trace:trace_dev_password@localhost:15434/postgres"
)
DEFAULT_DB_NAME = "scorecard_store"


def get_server_url() -> str:
    return os.getenv("SCORECARD_SERVER_URL", DEFAULT_SERVER_URL)


def get_db_name() -> str:
    return os.getenv("SCORECARD_DB_NAME", DEFAULT_DB_NAME)


def get_database_url() -> str:
    explicit = os.getenv("SCORECARD_DATABASE_URL")
    if explicit:
        return explicit
    server = get_server_url()
    return server.rsplit("/", 1)[0] + "/" + get_db_name()


def ensure_database() -> None:
    """Create the logical scorecard database on the existing PG server if absent."""
    server_engine = create_engine(get_server_url(), isolation_level="AUTOCOMMIT")
    try:
        with server_engine.connect() as conn:
            conn.execute(text(f'CREATE DATABASE "{get_db_name()}"'))
            print(f"created database {get_db_name()}")
    except ProgrammingError as exc:
        if "already exists" not in str(exc).lower():
            raise
    finally:
        server_engine.dispose()


engine = None


def get_engine():
    global engine
    if engine is None:
        engine = create_engine(get_database_url(), pool_pre_ping=True)
    return engine


SessionLocal = None


def get_session_factory():
    global SessionLocal
    if SessionLocal is None:
        SessionLocal = sessionmaker(autocommit=False, autoflush=False,
                                    bind=get_engine())
    return SessionLocal


def get_db():
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()
