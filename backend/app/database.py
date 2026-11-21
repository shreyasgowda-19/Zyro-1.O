import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

# Engine configuration with SQLite optimizations
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {
        "check_same_thread": False,
        "timeout": 15
    }

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

# Enforce SQLite foreign keys, WAL mode, and busy timeout
if settings.DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_append_only_triggers(conn):
    """Create triggers on audit_log and review_case_actions to prevent UPDATE and DELETE."""
    conn.execute("""
    CREATE TRIGGER IF NOT EXISTS abort_audit_log_update
    BEFORE UPDATE ON audit_log
    BEGIN
        SELECT RAISE(ABORT, 'append-only table: updates forbidden');
    END;
    """)
    conn.execute("""
    CREATE TRIGGER IF NOT EXISTS abort_audit_log_delete
    BEFORE DELETE ON audit_log
    BEGIN
        SELECT RAISE(ABORT, 'append-only table: deletions forbidden');
    END;
    """)
    conn.execute("""
    CREATE TRIGGER IF NOT EXISTS abort_review_case_action_update
    BEFORE UPDATE ON review_case_actions
    BEGIN
        SELECT RAISE(ABORT, 'append-only table: updates forbidden');
    END;
    """)
    conn.execute("""
    CREATE TRIGGER IF NOT EXISTS abort_review_case_action_delete
    BEFORE DELETE ON review_case_actions
    BEGIN
        SELECT RAISE(ABORT, 'append-only table: deletions forbidden');
    END;
    """)
