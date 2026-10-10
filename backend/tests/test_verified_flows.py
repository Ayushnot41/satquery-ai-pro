import secrets
import numpy as np
from fastapi.testclient import TestClient
from app.main import app
from app.api.auth import PHONES, digest
from app.core.database import DurableStore
from app.geospatial.export import grounded_features
from app.agents.visual_grounding import VisualGroundingAgent
from app.schemas.agents import ChangeRegion, GroundingResult
from app.schemas.investigation import InvestigationResponse
from tests.test_pro_security import account


def test_blank_image_does_not_invent_a_grounded_region():
    assert VisualGroundingAgent()._saliency_grounding_regions(np.zeros((128, 128, 3)), 'Find buildings') == []


def test_geojson_uses_source_transform_and_rejects_demo_coordinates():
    inv = InvestigationResponse(investigation_id='geo-test', status='complete', question='Compare scene',
        provenance={'mode':'provider','image_georeferencing':{'crs':'EPSG:4326','transform':[0.01,0,70,0,-0.01,30],'width':100,'height':100}},
        grounding=GroundingResult(regions=[ChangeRegion(bbox=[0.1,0.2,0.3,0.4],coordinate_space='normalized')]))
    features, _ = grounded_features(inv)
    ring = features[0]['geometry']['coordinates'][0]
    assert ring[0] == ring[-1]
    assert min(x for x, y in ring) == 70.1
    assert max(y for x, y in ring) == 29.8
    inv.provenance['mode'] = 'simulation'
    assert grounded_features(inv)[0] == []


def test_phone_login_single_use_and_no_cross_account_rebinding():
    phone = '+1555' + ''.join(str(secrets.randbelow(10)) for _ in range(7))
    with TestClient(app) as first, TestClient(app) as second:
        email, _ = account(first)
        sent = first.post('/api/auth/otp/send', json={'phone':phone,'purpose':'verification'}).json()
        verified = first.post('/api/auth/otp/verify', json={'phone':phone,'otp':sent['development_code']})
        assert verified.status_code == 200
        first.post('/api/auth/logout', json={})
        sends=DurableStore('phone_sends',global_scope=True)
        pending=sends[digest(phone)];pending['sent_at']-=31;sends[digest(phone)]=pending
        sent = first.post('/api/auth/otp/send', json={'phone':phone,'purpose':'login'}).json()
        payload={'phone':phone,'otp':sent['development_code'],'purpose':'login'}
        assert first.post('/api/auth/otp/verify',json=payload).json()['user']['email'] == email
        assert first.post('/api/auth/otp/verify',json=payload).status_code == 400
        account(second)
        pending=sends[digest(phone)];pending['sent_at']-=31;sends[digest(phone)]=pending
        other=second.post('/api/auth/otp/send',json={'phone':phone}).json()
        assert second.post('/api/auth/otp/verify',json={'phone':phone,'otp':other['development_code']}).status_code == 409
        assert PHONES[digest(phone)]['email'] == email
