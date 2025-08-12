import os,  requests
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

OCID_KEY = os.environ.get("OCID_KEY")

def _normalize_cells(raw):
    """
    Dönen gövde hangi şemada olursa olsun tek tipe getir:
    {
      "cells": [
        {"lat": float, "lon": float, "radio": str, "mcc": int, "mnc": int, "lac": int, "cellid": int, "range": int, "updated": str, ...}
      ]
    }
    """
    try:
        # Birkaç olası kök
        candidates = []
        if isinstance(raw, dict):
            for key in ("cells", "results", "data", "items"):
                if isinstance(raw.get(key), list):
                    candidates = raw.get(key)
                    break
        if not candidates and isinstance(raw, list):
            candidates = raw

        cells = []
        for c in candidates:
            # Çeşitli alan adlarını normalize et
            lat = c.get("lat") or c.get("latitude") or c.get("latDeg")
            lon = c.get("lon") or c.get("lng") or c.get("long") or c.get("longitude") or c.get("lonDeg")
            if lat is None or lon is None:
                continue
            try:
                lat = float(lat)
                lon = float(lon)
            except (TypeError, ValueError):
                continue

            cells.append({
                "lat": lat,
                "lon": lon,
                "radio": c.get("radio") or c.get("tech") or c.get("technology"),
                "mcc": c.get("mcc") or c.get("MCC"),
                "mnc": c.get("mnc") or c.get("MNC"),
                "lac": c.get("lac") or c.get("LAC") or c.get("tac") or c.get("enbid"),
                "cellid": c.get("cellid") or c.get("cid") or c.get("ecid") or c.get("ncid"),
                "range": c.get("range") or c.get("coverage") or c.get("radius"),
                "updated": c.get("updated") or c.get("last_seen") or c.get("last_update"),
            })
        return {"cells": cells}
    except Exception:
        # Son çare: hiç dokunmadan sarmala
        return {"cells": []}

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def towers_in_bbox(request):
    bbox = request.GET.get('bbox')
    if not bbox:
        return JsonResponse({'error': 'bbox gerekli'}, status=400)

    if not OCID_KEY:
        return JsonResponse({'error': 'OCID_KEY tanımlı değil (server ortam değişkeni).'}, status=500)

    try:
        # Bazı API’ler 'bbox', bazıları 'BBOX' kabul ediyor; ikisini de gönder.
        params = {
            'key': OCID_KEY,
            'BBOX': bbox,
            'bbox': bbox,
            'format': 'json',
        }

        r = requests.get(
            "https://opencellid.org/cell/getInArea",
            params=params,
            timeout=12
        )

        content_type = r.headers.get("Content-Type", "")
        # 200 değilse ya da JSON değilse ham hata döndür
        if r.status_code != 200:
            payload = None
            try:
                payload = r.json()
            except Exception:
                payload = {"text": r.text[:500]}
            return JsonResponse({
                "error": "Upstream error",
                "status": r.status_code,
                "upstream": payload,
                "sent_params": params
            }, status=502)

        # JSON değilse (ör. HTML döndüyse) yakala
        if "json" not in content_type.lower():
            return JsonResponse({
                "error": "Upstream non-JSON response",
                "status": r.status_code,
                "content_type": content_type,
                "snippet": r.text[:500]
            }, status=502)

        raw = r.json()
        normalized = _normalize_cells(raw)
        return JsonResponse(normalized, status=200, safe=False)

    except requests.Timeout:
        return JsonResponse({'error': 'OpenCellID timeout'}, status=504)
    except Exception as e:
        return JsonResponse({'error': f'proxy-failure: {str(e)}'}, status=502)
