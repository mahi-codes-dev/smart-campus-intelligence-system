from contextlib import contextmanager
import atexit

import psycopg2
from psycopg2.pool import ThreadedConnectionPool

from config import settings


_DB_POOL = None


class PooledConnectionProxy:
    def __init__(self, conn):
        self._conn = conn
        self._released = False

    def close(self):
        if not self._released:
            release_db_connection(self._conn)
            self._released = True

    def __getattr__(self, item):
        return getattr(self._conn, item)


def _build_connect_kwargs():
    if settings.database_url:
        return {"dsn": settings.database_url}

    return {
        "host": settings.db_host,
        "database": settings.db_name,
        "user": settings.db_user,
        "password": settings.db_password,
        "port": settings.db_port,
    }


def get_db_pool():
    global _DB_POOL

    if _DB_POOL is None:
        _DB_POOL = ThreadedConnectionPool(
            minconn=settings.db_pool_minconn,
            maxconn=settings.db_pool_maxconn,
            **_build_connect_kwargs(),
        )

    return _DB_POOL


def close_db_pool():
    global _DB_POOL

    if _DB_POOL is not None:
        _DB_POOL.closeall()
        _DB_POOL = None


atexit.register(close_db_pool)


def get_db_connection():
    return PooledConnectionProxy(get_db_pool().getconn())


def release_db_connection(conn, *, close=False):
    if conn is None:
        return

    raw_conn = getattr(conn, "_conn", conn)

    if close:
        raw_conn.close()
        return

    get_db_pool().putconn(raw_conn)


@contextmanager
def db_connection(commit=False):
    conn = get_db_connection()

    try:
        yield conn
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


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
