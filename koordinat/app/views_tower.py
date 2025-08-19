import os, math, logging, requests, json
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

from django.http import JsonResponse
from django.core.cache import cache
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

logger = logging.getLogger(__name__)

def _mask_key_in_url(full_url: str) -> str:
    try:
        u = urlparse(full_url)
        q = dict(parse_qsl(u.query, keep_blank_values=True))
        if 'key' in q:
            q['key'] = '****'
        new_q = urlencode(q)
        return urlunparse((u.scheme, u.netloc, u.path, u.params, new_q, u.fragment))
    except Exception:
        return full_url

def _is_lat(v: float) -> bool:
    return -90.0 <= v <= 90.0

def _is_lon(v: float) -> bool:
    return -180.0 <= v <= 180.0

def _parse_bbox_str(bbox_str: str):
    """
    Desteklenen giriş formatları:
      - LAT1,LON1,LAT2,LON2
      - LON1,LAT1,LON2,LAT2
    Çıkış: (sw_lat, sw_lon, ne_lat, ne_lon)
    """
    try:
        a, b, c, d = [float(x) for x in bbox_str.split(',')]
    except Exception:
        return None

    # Heuristik: hangi sıra?
    # Senaryo A: LAT,LON,LAT,LON
    if _is_lat(a) and _is_lon(b) and _is_lat(c) and _is_lon(d):
        lat1, lon1, lat2, lon2 = a, b, c, d
    # Senaryo B: LON,LAT,LON,LAT
    elif _is_lon(a) and _is_lat(b) and _is_lon(c) and _is_lat(d):
        lon1, lat1, lon2, lat2 = a, b, c, d
    else:
        return None

    if not (_is_lat(lat1) and _is_lat(lat2) and _is_lon(lon1) and _is_lon(lon2)):
        return None

    sw_lat, ne_lat = sorted([lat1, lat2])
    sw_lon, ne_lon = sorted([lon1, lon2])
    return sw_lat, sw_lon, ne_lat, ne_lon

def _norm_bbox_key(sw_lat, sw_lon, ne_lat, ne_lon, ndigits=4):
    # Yakın istekleri grupla (4 ~ 11 m civarı)
    sw_lat = round(sw_lat, ndigits); sw_lon = round(sw_lon, ndigits)
    ne_lat = round(ne_lat, ndigits); ne_lon = round(ne_lon, ndigits)
    # OCID BBOX sırası: LON,LAT,LON,LAT
    bbox_param = f"{sw_lon},{sw_lat},{ne_lon},{ne_lat}"
    key = f"ocid:{bbox_param}"
    return key, bbox_param

@api_view(['GET'])
@permission_classes([AllowAny])
def towers_in_bbox(request):
    OCID_KEY = os.environ.get("OCID_KEY")
    if not OCID_KEY:
        return JsonResponse({'error': 'OCID_KEY ortam değişkeni tanımlı değil.'}, status=500)

    bbox_str = request.GET.get('bbox')
    if not bbox_str:
        return JsonResponse({'error': 'bbox gerekli'}, status=400)

    parsed = _parse_bbox_str(bbox_str)
    if not parsed:
        return JsonResponse({'error': 'bbox formatı LAT1,LON1,LAT2,LON2 veya LON1,LAT1,LON2,LAT2 olmalı'}, status=400)

    sw_lat, sw_lon, ne_lat, ne_lon = parsed

    # Alan kontrolü (~4 km²)
    try:
        mid_lat = (sw_lat + ne_lat) / 2.0
        dy_m = (ne_lat - sw_lat) * 111_000
        dx_m = (ne_lon - sw_lon) * 111_000 * math.cos(math.radians(mid_lat))
        area_m2 = abs(dx_m * dy_m)
        if area_m2 > 4_000_000:
            return JsonResponse({'error': 'bbox çok geniş (max ~4 km²).'}, status=400)
    except Exception:
        pass

    # Cache anahtarı + doğru OCID BBOX sırası
    cache_key, bbox_param = _norm_bbox_key(sw_lat, sw_lon, ne_lat, ne_lon, ndigits=4)
    ttl_seconds = 60 * 60  # 1 saat

    # 1) CACHE HIT?
    cached = cache.get(cache_key)
    if cached is not None:
        # KOPYA ÜZERİNDE flag ekle (cache objesini mutasyona uğratma)
        try:
            if isinstance(cached, dict):
                payload = dict(cached)
            else:
                payload = json.loads(json.dumps(cached))
        except Exception:
            payload = cached
        payload['_cache'] = True
        return JsonResponse(payload, status=200)

    # 2) CACHE MISS → OCID'e git
    try:
        r = requests.get(
            "https://opencellid.org/cell/getInArea",
            params={'key': OCID_KEY, 'BBOX': bbox_param, 'format': 'json'},
            timeout=15
        )

        # Log’da anahtarı maskele
        logger.info("[OCID] %s -> %s", _mask_key_in_url(r.url), r.status_code)

        if r.status_code != 200:
            return JsonResponse({
                'error': 'OpenCellID non-200',
                'status': r.status_code,
                'url': _mask_key_in_url(r.url),
                'body': r.text[:500],
            }, status=r.status_code)

        try:
            data = r.json()
        except ValueError:
            return JsonResponse({
                'error': 'OpenCellID JSON döndürmedi',
                'status': r.status_code,
                'url': _mask_key_in_url(r.url),
                'body': r.text[:500],
            }, status=502)

        if isinstance(data, dict):
            data = dict(data)  # kopya
            data['_debug_url'] = _mask_key_in_url(r.url)
        else:
            data = {'data': data, '_debug_url': _mask_key_in_url(r.url)}

        # CACHE SET
        cache.set(cache_key, data, ttl_seconds)

        return JsonResponse(data, status=200)

    except requests.Timeout:
        return JsonResponse({'error': 'OpenCellID zaman aşımı'}, status=504)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=502)
