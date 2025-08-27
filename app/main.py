<<<<<<< HEAD
﻿# app/main.py
import os
import traceback
from fastapi import FastAPI, Request
=======
﻿import os
import traceback
from fastapi import FastAPI, Request, Form
>>>>>>> ac2cfa8 (final commit - updated code)
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from .utils import build_response

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
<<<<<<< HEAD
# Set ALLOWED_ORIGINS on Azure to your site, e.g.
# "https://<your-webapp>.azurewebsites.net,https://www.yourdomain.com"
_raw = os.getenv("ALLOWED_ORIGINS", "")
_allowed = [o.strip() for o in _raw.split(",") if o.strip()]

# Add helpful defaults for local dev
_allowed += ["http://localhost", "http://127.0.0.1", "http://localhost:8000", "http://127.0.0.1:8000"]

# If deploying on Render, Render injects RENDER_EXTERNAL_HOSTNAME
render_host = os.getenv("RENDER_EXTERNAL_HOSTNAME", "").strip()
if render_host:
    _allowed.append(f"https://{render_host}")

# If deploying on Azure App Service, add your webapp host if you know it
azure_app = os.getenv("AZURE_WEBAPP_HOSTNAME", "").strip()   # e.g. set to myapp.azurewebsites.net
if azure_app:
    _allowed.append(f"https://{azure_app}")

# Deduplicate
ALLOWED_ORIGINS = sorted(set([o for o in _allowed if o]))

app = FastAPI(title="Flight Path Safety")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,      # explicit list is best
    allow_origin_regex = r"https://.*\.onrender\.com$|https://.*\.azurewebsites\.net$"  # optional: allow any *.onrender.com
    allow_credentials=False,            # keep False unless you truly need cookies/auth
=======

app = FastAPI(title="Flight Path Safety")

# CORS (keep permissive or restrict in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
>>>>>>> ac2cfa8 (final commit - updated code)
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

<<<<<<< HEAD
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

=======

# ---------- UI (single page) ----------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    # Empty page with just the form
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "form_departure": "", "form_arrival": "", "result": None, "error": None}
    )


@app.post("/analyze", response_class=HTMLResponse)
async def analyze_html(
    request: Request,
    departure: str = Form(...),
    arrival: str = Form(...),
):
    dep = departure.strip()
    arr = arrival.strip()
    error = None
    result = None

    api_key = OPENWEATHER_API_KEY
    if not api_key:
        error = "OPENWEATHER_API_KEY is missing on the server."
    else:
        try:
            result = build_response(dep, arr, api_key, airports_csv_path="app/airports_data.csv")
            if "error" in result:
                error = result["error"]
                result = None
        except Exception as e:
            err = "".join(traceback.format_exception_only(type(e), e)).strip()
            error = f"Internal Server Error: {err}"

    # Render the same template: form at top, results below
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "form_departure": dep, "form_arrival": arr, "result": result, "error": error},
        status_code=200 if not error else 400
    )


# ---------- JSON API (unchanged) ----------
>>>>>>> ac2cfa8 (final commit - updated code)
@app.post("/api/analyze", response_class=JSONResponse)
async def analyze(req: Request):
    try:
        body = await req.json()
    except Exception:
        return JSONResponse({"error": "Request body must be JSON."}, status_code=400)

    try:
        dep = (body.get("departure") or "").strip()
        arr = (body.get("arrival") or "").strip()
        api_key = OPENWEATHER_API_KEY or (body.get("apiKey") or "").strip()

        if not api_key:
            return JSONResponse({"error": "OPENWEATHER_API_KEY missing."}, status_code=400)
        if not dep or not arr:
            return JSONResponse({"error": "Both 'departure' and 'arrival' are required."}, status_code=400)

        result = build_response(dep, arr, api_key, airports_csv_path="app/airports_data.csv")
        if "error" in result:
            return JSONResponse(result, status_code=400)

        return JSONResponse(result, status_code=200)

    except Exception as e:
        err = "".join(traceback.format_exception_only(type(e), e)).strip()
        return JSONResponse({"error": f"Internal Server Error: {err}"}, status_code=500)

<<<<<<< HEAD
=======

>>>>>>> ac2cfa8 (final commit - updated code)
@app.get("/healthz", response_class=PlainTextResponse)
async def healthz():
    return "ok"
