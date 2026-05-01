from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
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
            "search_terms": name,
            "ad_reached_countries": "ES",
            "ad_type": "ALL",
            "fields": "page_name,ad_snapshot_url,ad_delivery_start_time,ad_delivery_stop_time",
            "access_token": token,
            "limit": 5
        }

        resp = requests.get(url, params=params)
        data = resp.json()

        ads = data.get("data", [])
        results.append({
            "name": name,
            "has_ads": len(ads) > 0,
            "ads": ads
        })

    return results