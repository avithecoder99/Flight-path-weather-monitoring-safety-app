import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .utils import build_response

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")

app = FastAPI(title="Flight Path Safety")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/analyze", response_class=JSONResponse)
async def analyze(req: Request):
    body = await req.json()
    dep = body.get("departure", "").strip()
    arr = body.get("arrival", "").strip()
    api_key = OPENWEATHER_API_KEY or body.get("apiKey", "")
    if not api_key:
        return JSONResponse({"error": "OPENWEATHER_API_KEY missing."}, status_code=400)
    result = build_response(dep, arr, api_key, airports_csv_path="app/airports_data.csv")
    if "error" in result:
        return JSONResponse(result, status_code=400)
    return JSONResponse(result)
