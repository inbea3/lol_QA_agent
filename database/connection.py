from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

import psycopg2
from psycopg2.extensions import connection

from config.settings import settings


@contextmanager
def md_connection() -> Generator[connection, None, None]:
    conn = psycopg2.connect(settings.md_db.dsn)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def vector_connection() -> Generator[connection, None, None]:
    conn = psycopg2.connect(settings.vector_db.dsn)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
