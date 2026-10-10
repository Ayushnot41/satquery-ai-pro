"""Transactional identity helpers; old email-keyed accounts remain readable."""
from contextlib import contextmanager
import hashlib
from sqlalchemy import select, text
from .database import engine, Record


def account_key(user):
    return user.get('_key') or user['email']


def reference_key(reference):
    return reference.get('user_key') or reference.get('email')


@contextmanager
def identity_transaction(lock_key):
    """Serialize an identity operation across processes, including first insertion."""
    with engine.connect() as conn:
        if engine.dialect.name == 'sqlite':
            conn.exec_driver_sql('BEGIN IMMEDIATE')
        else:
            conn.begin()
            lock_id = int.from_bytes(hashlib.sha256(lock_key.encode()).digest()[:8], 'big', signed=True)
            conn.execute(text('SELECT pg_advisory_xact_lock(:key)'), {'key': lock_id})
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise


def record_conditions(namespace, key):
    return (Record.namespace == namespace, Record.owner == 'system', Record.key == key)


def read_record(conn, namespace, key):
    return conn.execute(select(Record.value).where(*record_conditions(namespace, key)).with_for_update()).scalar_one_or_none()
