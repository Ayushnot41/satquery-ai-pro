"""Keep legacy demonstrations available with explicit machine-readable provenance."""
import json
from fastapi.routing import APIRoute

class SimulationRoute(APIRoute):
    def get_route_handler(self):
        original = super().get_route_handler()
        async def handler(request):
            response = await original(request)
            if response.status_code < 400 and 'application/json' in response.headers.get('content-type', ''):
                body = json.loads(response.body)
                if isinstance(body, dict):
                    body['provenance'] = {'mode': 'simulation', 'scientifically_validated': False,
                        'notice': 'Illustrative scenario output. Not verified sensor observations or an operational assessment.'}
                    response.body = json.dumps(body, ensure_ascii=False).encode()
                    response.headers['content-length'] = str(len(response.body))
                response.headers['X-Data-Mode'] = 'simulation'
            return response
        return handler
