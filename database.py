from contextlib import contextmanager
import psycopg2

from config import settings

def get_db_connection():
    if settings.database_url:
        return psycopg2.connect(settings.database_url)

    return psycopg2.connect(
        host=settings.db_host,
        database=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
        port=settings.db_port,
    )


@contextmanager
def db_cursor(commit=True):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        yield cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()
