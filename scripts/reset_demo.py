import os
import sys
import time

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, backend_dir)

from app.config import settings

def reset_demo():
    start_time = time.time()
    print("Resetting PayGuard 360 demo database...")

    # Determine sqlite db path from settings.DATABASE_URL
    url = settings.DATABASE_URL
    if url.startswith("sqlite:///"):
        db_path = url[len("sqlite:///"):]
    elif url.startswith("sqlite://"):
        db_path = url[len("sqlite://"):]
    else:
        db_path = os.path.join(backend_dir, "payguard.db")

    # Dispose any active engine connections before removing file on Windows
    try:
        from app.database import engine
        engine.dispose()
    except Exception:
        pass
    import gc
    gc.collect()

    # Clean existing database files
    file_removed = True
    for ext in ["", "-wal", "-shm"]:
        target_file = db_path + ext
        if os.path.exists(target_file):
            try:
                os.remove(target_file)
            except Exception as e:
                file_removed = False

    # If file removal was blocked by Windows file lock, drop all tables cleanly
    if not file_removed and os.path.exists(db_path):
        try:
            import sqlite3
            c = sqlite3.connect(db_path)
            c.execute("PRAGMA foreign_keys = OFF;")
            tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence'").fetchall()]
            for t in tables:
                c.execute(f"DROP TABLE IF EXISTS \"{t}\";")
            c.commit()
            c.close()
        except Exception as e:
            print(f"Table drop fallback warning: {e}")

    # Run alembic upgrade head
    from alembic.config import Config
    from alembic import command
    alembic_ini_path = os.path.join(backend_dir, "alembic.ini")
    alembic_cfg = Config(alembic_ini_path)
    alembic_cfg.set_main_option("script_location", os.path.join(backend_dir, "migrations"))
    alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    command.upgrade(alembic_cfg, "head")

    # Install append-only triggers
    import sqlite3
    from app.database import create_append_only_triggers
    conn = sqlite3.connect(db_path)
    create_append_only_triggers(conn)
    conn.commit()
    conn.close()

    # Seed demo data
    from scripts.seed_demo import seed_database
    seed_database()

    elapsed = time.time() - start_time
    print(f"Demo reset completed successfully in {elapsed:.2f} seconds! (Target: < 5.0s)")
    return elapsed

if __name__ == "__main__":
    reset_demo()
