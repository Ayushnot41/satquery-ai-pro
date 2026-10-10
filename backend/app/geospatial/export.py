"""Export pixel evidence only when the source supplies a geographic transform."""
import math
from pyproj import Transformer


def grounded_features(investigation):
    geo = investigation.provenance.get('image_georeferencing', {})
    if investigation.provenance.get('mode') == 'simulation' or not geo.get('crs') or not geo.get('transform'):
        return [], 'No source georeferencing. Pixel evidence is retained in the JSON report.'
    regions = investigation.grounding.regions if investigation.grounding else []
    if not regions and investigation.change_result:
        regions = investigation.change_result.change_regions
    features = []
    try:
        a, b, c, d, e, f = geo['transform'][:6]
        width, height = geo['width'], geo['height']
        transform = Transformer.from_crs(geo['crs'], 'EPSG:4326', always_xy=True)
        for region in regions:
            x1, y1, x2, y2 = region.bbox
            if region.coordinate_space == 'normalized':
                x1, x2, y1, y2 = x1 * width, x2 * width, y1 * height, y2 * height
            if not (0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height):
                continue
            corners = [(x1, y1), (x1, y2), (x2, y2), (x2, y1)]
            ring = [list(transform.transform(a*x+b*y+c, d*x+e*y+f)) for x, y in corners]
            if not all(math.isfinite(lon) and math.isfinite(lat) and -180 <= lon <= 180 and -90 <= lat <= 90 for lon, lat in ring):
                continue
            # Do not draw a misleading polygon across the world at the antimeridian.
            if max(p[0] for p in ring) - min(p[0] for p in ring) > 180:
                continue
            signed = sum(ring[i][0]*ring[(i+1)%4][1]-ring[(i+1)%4][0]*ring[i][1] for i in range(4))
            if signed < 0:
                ring.reverse()
            ring.append(ring[0][:])
            features.append({'type': 'Feature', 'geometry': {'type': 'Polygon', 'coordinates': [ring]},
                'properties': {'label': region.change_type, 'area_pixels': region.area_pixels,
                    'investigation_id': investigation.investigation_id, 'scientifically_validated': False,
                    'coordinate_source': 'source raster affine transform'}})
    except (ValueError, TypeError, KeyError):
        return [], 'Source georeferencing could not be transformed. Use the pixel evidence JSON.'
    return features, 'Coordinates derived from source metadata; model findings require independent review.' if features else 'No supported grounded region could be georeferenced.'
