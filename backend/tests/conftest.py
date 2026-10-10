"""All tests run against isolated temporary storage, never a user's workspace."""
import os, tempfile
from pathlib import Path
import pytest
test_root=Path(tempfile.mkdtemp(prefix='satquery-pro-tests-'))
os.environ['DATABASE_URL']='sqlite:///'+(test_root/'test.db').as_posix()
os.environ['UPLOAD_DIR']=str(test_root/'uploads')
os.environ['ENVIRONMENT']='test'
os.environ['DEMO_MODE']='true'
os.environ['VLM_BACKEND']='demo'
os.environ['DEVELOPMENT_VERIFICATION_CODES']='true'
os.environ['AUTH_PEPPER']='test-only-random-independent-auth-pepper-987654321'

@pytest.fixture(autouse=True)
def isolate_rate_buckets():
    from app.core.database import engine
    from app.core.guard import RateBucket
    from sqlalchemy import delete
    with engine.begin() as conn:
        conn.execute(delete(RateBucket))

