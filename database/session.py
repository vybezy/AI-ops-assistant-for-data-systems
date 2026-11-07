from contextlib import contextmanager

import psycopg2

from database.config import config

@contextmanager
def db_connection():
    """
    opens a PostgreSQL connection for one transaction.
    commits if the block succeeds, rolls back if it raises,
    and always closes the connection, so no code path can leak one.
    """
    conn = psycopg2.connect(**config())
    try:
        yield conn
        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()
