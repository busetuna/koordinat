import os, math, logging, requests
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

logger = logging.getLogger(__name__)

def _parse_bbox_str(bbox_str):
    try:
        lat1, lon1, lat2, lon2 = [float(x) for x in bbox_str.split(',')]
        sw_lat, ne_lat = sorted([lat1, lat2])
        sw_lon, ne_lon = sorted([lon1, lon2])
        return sw_lat, sw_lon, ne_lat, ne_lon
    except Exception:
        return None

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
        return JsonResponse({'error': 'bbox formatı LAT1,LON1,LAT2,LON2 olmalı'}, status=400)

    sw_lat, sw_lon, ne_lat, ne_lon = parsed
    # ✅ Doğru sıra: LON,LAT,LON,LAT
    bbox_param = f"{sw_lon},{sw_lat},{ne_lon},{ne_lat}"

    try:
        mid_lat = (sw_lat + ne_lat) / 2.0
        dy_m = (ne_lat - sw_lat) * 111_000
        dx_m = (ne_lon - sw_lon) * 111_000 * math.cos(math.radians(mid_lat))
        area_m2 = abs(dx_m * dy_m)
        if area_m2 > 4_000_000:
            return JsonResponse({'error': 'bbox çok geniş (max ~4 km²).'}, status=400)
    except Exception:
        pass

    try:
        r = requests.get(
            "https://opencellid.org/cell/getInArea",
            params={'key': OCID_KEY, 'BBOX': bbox_param, 'format': 'json'},
            timeout=15
        )
        logger.info("[OCID] %s -> %s", r.url, r.status_code)
       
        try:
            data = r.json()
        except ValueError:
            data = {'error': 'OpenCellID JSON döndürmedi',
                    'body': r.text[:500],
                    }

        if r.status_code != 200:
            return JsonResponse({
                'error': 'OpenCellID non-200',
                'status': r.status_code,
                'url': r.url,
                'body': r.text[:1000],
            }, status=r.status_code)

        try:
            data = r.json()
        except ValueError:
            return JsonResponse({
                'error': 'OpenCellID JSON döndürmedi',
                'status': r.status_code,
                'url': r.url,
                'body': r.text[:1000],
                "cells": data.get("cells", []) if isinstance(data, dict) else []
            }, status=502)

        data['_debug_url'] = r.url  # isteğe bağlı
        return JsonResponse(data, status=200, safe=False)

    except requests.Timeout:
        return JsonResponse({'error': 'OpenCellID zaman aşımı'}, status=504)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=502)
