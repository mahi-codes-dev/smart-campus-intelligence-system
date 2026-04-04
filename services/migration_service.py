from hashlib import sha256
from pathlib import Path

from database import get_db_connection


MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def _ensure_migrations_table(cur):
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id SERIAL PRIMARY KEY,
            filename VARCHAR(255) NOT NULL UNIQUE,
            checksum VARCHAR(64) NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def run_migrations():
    if not MIGRATIONS_DIR.exists():
        return []

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        _ensure_migrations_table(cur)
        cur.execute("SELECT filename, checksum FROM schema_migrations")
        applied = {row[0]: row[1] for row in cur.fetchall()}
        executed = []

        for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
            filename = path.name
            checksum = sha256(path.read_bytes()).hexdigest()

            if filename in applied:
                if applied[filename] != checksum:
                    raise RuntimeError(
                        f"Migration {filename} has changed after being applied. "
                        "Create a new migration instead of editing the old one."
                    )
                continue

            cur.execute(path.read_text(encoding="utf-8"))
            cur.execute(
                """
                INSERT INTO schema_migrations (filename, checksum)
                VALUES (%s, %s)
                """,
                (filename, checksum),
            )
            executed.append(filename)

        conn.commit()
        return executed
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()
