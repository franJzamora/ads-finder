from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import openpyxl
import requests
import io
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/search")
async def search_ads(file: UploadFile = File(...)):
    token = os.environ.get("META_TOKEN")
    if not token:
        return JSONResponse(status_code=500, content={"error": "Token de Meta no configurado en el servidor."})

    contents = await file.read()
    wb = openpyxl.load_workbook(io.BytesIO(contents))
    ws = wb.active

    results = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        name = row[0]
        if not name:
            continue

        url = "https://graph.facebook.com/v19.0/ads_archive"
        params = {
            "search_terms": str(name).strip(),
            "ad_reached_countries": "ES",
            "ad_type": "ALL",
            "fields": "page_name,ad_snapshot_url,ad_delivery_start_time,ad_delivery_stop_time",
            "access_token": token,
            "limit": 10
        }

        try:
            resp = requests.get(url, params=params, timeout=15)
            data = resp.json()

            if "error" in data:
                results.append({
                    "name": name,
                    "has_ads": False,
                    "ads": [],
                    "error": data["error"].get("message", "Error desconocido")
                })
                continue

            ads = data.get("data", [])
            results.append({
                "name": name,
                "has_ads": len(ads) > 0,
                "ads": ads,
                "error": None
            })
        except Exception as e:
            results.append({
                "name": name,
                "has_ads": False,
                "ads": [],
                "error": str(e)
            })

    return results