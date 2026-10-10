"""Durable, owner-scoped records. SQLite for local use; PostgreSQL for deployment."""
from collections.abc import MutableMapping
from contextvars import ContextVar
from pathlib import Path
from typing import Any
from sqlalchemy import JSON, String, create_engine, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from .config import settings

Path('data').mkdir(exist_ok=True)
url = settings.database_url or 'sqlite:///./data/satquery-pro.db'
engine = create_engine(url, pool_pre_ping=True, connect_args={'check_same_thread': False, 'timeout': 30} if url.startswith('sqlite:') else {})

class Base(DeclarativeBase):
    pass

class Record(Base):
    __tablename__ = 'workspace_records'
    namespace: Mapped[str] = mapped_column(String(60), primary_key=True)
    owner: Mapped[str] = mapped_column(String(100), primary_key=True)
    key: Mapped[str] = mapped_column(String(320), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON)

def initialize_schema():
    """Serialize first-run DDL across API and worker processes."""
    with engine.connect() as connection:
        if engine.dialect.name == 'sqlite':
            connection.exec_driver_sql('BEGIN IMMEDIATE')
        else:
            connection.begin()
            connection.execute(text('SELECT pg_advisory_xact_lock(718294613)'))
        try:
            Base.metadata.create_all(connection)
            connection.commit()
        except Exception:
            connection.rollback()
            raise

initialize_schema()
owner_id: ContextVar[str] = ContextVar('owner_id', default='public-demo')

class DurableStore(MutableMapping):
    def __init__(self, namespace: str, model=None, global_scope=False):
        self.namespace, self.model, self.global_scope = namespace, model, global_scope

    def identity(self, key):
        return self.namespace, 'system' if self.global_scope else owner_id.get(), str(key)

    def __getitem__(self, key):
        with Session(engine) as db:
            row = db.get(Record, self.identity(key))
            if row is None:
                raise KeyError(key)
            return self.model.model_validate(row.value) if self.model else row.value

    def __setitem__(self, key, value):
        payload = value.model_dump(mode='json') if hasattr(value, 'model_dump') else value
        with Session(engine) as db, db.begin():
            ns, owner, item = self.identity(key)
            db.merge(Record(namespace=ns, owner=owner, key=item, value=payload))

    def __delitem__(self, key):
        with Session(engine) as db, db.begin():
            row = db.get(Record, self.identity(key))
            if row is None:
                raise KeyError(key)
            db.delete(row)

    def __iter__(self):
        ns, owner, _ = self.identity('')
        with Session(engine) as db:
            return iter(list(db.scalars(select(Record.key).where(Record.namespace == ns, Record.owner == owner))))

    def __len__(self):
        return sum(1 for _ in self)

    def values(self):
        ns, owner, _ = self.identity('')
        with Session(engine) as db:
            rows = db.scalars(select(Record.value).where(Record.namespace == ns, Record.owner == owner)).all()
            return [self.model.model_validate(v) if self.model else v for v in rows]
