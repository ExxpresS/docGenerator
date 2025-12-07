import psycopg2
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from app.config import settings

# Pool de connexions
pool = None


def init_pool():
    """Initialise le pool de connexions"""
    global pool
    if pool is None:
        pool = SimpleConnectionPool(
            minconn=1,
            maxconn=20,
            dsn=settings.DATABASE_URL
        )


def close_pool():
    """Ferme le pool de connexions"""
    global pool
    if pool is not None:
        pool.closeall()
        pool = None


@contextmanager
def get_db():
    """Context manager pour connexion DB avec dict cursor"""
    if pool is None:
        init_pool()

    conn = pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


@contextmanager
def get_cursor():
    """Context manager pour cursor avec RealDictCursor"""
    with get_db() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            yield cursor
        finally:
            cursor.close()
