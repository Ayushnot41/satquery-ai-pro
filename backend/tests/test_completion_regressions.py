"""Regression coverage for defects found while completing the Pro workspace."""
import numpy as np
import pytest
from app.agents.orchestrator import InvestigationOrchestrator
from app.api.investigation import _get_or_create_demo_image
from app.geospatial.raster import extract_metadata
from app.models.demo_backend import DemoBackend
from app.schemas.imagery import ImageryInput, SensorType
from app.schemas.investigation import InvestigationRequest


@pytest.mark.asyncio
async def test_provider_failure_is_not_a_completed_finding(tmp_path, monkeypatch):
    from PIL import Image
    path = tmp_path / 'scene.png'
    Image.new('RGB', (64, 64)).save(path)
    backend = DemoBackend()
    async def failed(**kwargs):
        raise RuntimeError('provider secret must never reach the result')
    monkeypatch.setattr(backend, 'answer_question', failed)
    result = await InvestigationOrchestrator(backend).run_investigation(
        InvestigationRequest(question='Describe the scene', imagery_ids=['scene']),
        [ImageryInput(id='scene', path=str(path), metadata=extract_metadata(path, 'scene'), role='primary')],
        'provider-failure',
    )
    assert result.status == 'error'
    assert result.confidence is None
    assert result.fused_evidence is None
    assert result.total_duration_ms is not None
    assert 'provider secret' not in result.model_dump_json()


def test_generated_demo_is_reproducible(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = _get_or_create_demo_image('demo-repro-sar', SensorType.SAR)
    first = path.read_bytes()
    path.unlink()
    assert _get_or_create_demo_image('demo-repro-sar', SensorType.SAR).read_bytes() == first


@pytest.mark.asyncio
async def test_change_regions_use_the_resized_image_grid():
    from app.agents.change_detection import ChangeDetectionAgent
    from app.schemas.trace import ExecutionTrace
    before = np.zeros((80, 120, 3), dtype=np.uint8)
    after = np.zeros((160, 240, 3), dtype=np.uint8)
    after[40:120, 60:180] = 255
    result = await ChangeDetectionAgent().detect_changes(before, after, ExecutionTrace(investigation_id='resize'))
    assert result.has_change
    region = result.change_regions[0]
    assert region.coordinate_space == 'normalized'
    assert all(0 <= x <= 1 for x in region.bbox)
    assert region.bbox[0] == pytest.approx(0.25, abs=0.03)
    assert region.bbox[2] == pytest.approx(0.75, abs=0.03)


def test_concurrent_first_boot_initializes_schema(tmp_path):
    import os
    import subprocess
    import sys
    env = {**os.environ, 'DATABASE_URL': 'sqlite:///' + (tmp_path / 'boot.db').as_posix(),
           'UPLOAD_DIR': str(tmp_path / 'uploads')}
    processes = [subprocess.Popen([sys.executable, '-c', 'import app.api.jobs; import app.core.guard'],
                 env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(3)]
    for process in processes:
        _, error = process.communicate(timeout=45)
        assert process.returncode == 0, error


def test_public_preview_is_sample_only(monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.core.config import settings
    monkeypatch.setattr(settings, 'environment', 'preview')
    monkeypatch.setattr(settings, 'cookie_secure', True)
    monkeypatch.setattr(settings, 'development_verification_codes', False)
    monkeypatch.setattr(settings, 'cors_origins', 'https://preview.example')
    with TestClient(app, base_url='https://preview.example') as client:
        assert client.get('/api/auth/config').json()['public_preview']
        guest = client.post('/api/auth/guest-token', json={})
        assert guest.status_code == 200
        assert 'secure' in guest.headers['set-cookie'].lower()
        assert client.post('/api/auth/register', json={}).status_code == 403
        assert client.post('/api/imagery/upload', files={'file': ('x.png', b'fake')}).status_code == 403
        assert client.post('/api/jobs', json={'question': 'Describe this sample', 'imagery_ids': ['demo-construction-before']}).status_code == 202
        assert client.post('/api/auth/guest-token', headers={'Origin': 'https://other.example'}).status_code == 403


def test_public_preview_rejects_live_provider(monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.core.config import settings
    monkeypatch.setattr(settings, 'environment', 'preview')
    monkeypatch.setattr(settings, 'cookie_secure', True)
    monkeypatch.setattr(settings, 'development_verification_codes', False)
    monkeypatch.setattr(settings, 'cors_origins', 'https://preview.example')
    monkeypatch.setattr(settings, 'vlm_backend', 'gateway')
    with pytest.raises(RuntimeError, match='demo analysis only'):
        with TestClient(app):
            pass


@pytest.mark.asyncio
async def test_cancelled_running_job_does_not_save_a_report(monkeypatch):
    import uuid
    from sqlalchemy import update
    from app import worker
    from app.api.jobs import Job, submit_job, get_job
    from app.core.database import owner_id, engine, DurableStore
    from app.schemas.investigation import InvestigationResponse
    token = owner_id.set('cancel-test-' + uuid.uuid4().hex)
    try:
        job = submit_job(InvestigationRequest(question='Describe the sample', imagery_ids=['demo-construction-before']))
        async def cancel_during_run(request, persist=True):
            with engine.begin() as connection:
                connection.execute(update(Job).where(Job.id == job['id']).values(status='cancelled'))
            return InvestigationResponse(investigation_id='cancelled-report', status='complete', question=request.question)
        monkeypatch.setattr(worker, 'execute_investigation', cancel_during_run)
        assert await worker.process_one()
        assert get_job(job['id'])['status'] == 'cancelled'
        assert 'cancelled-report' not in DurableStore('investigations')
    finally:
        owner_id.reset(token)
