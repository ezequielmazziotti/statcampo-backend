"""
StatCampo — Backend API
FastAPI + httpx para proxy a api-football.com
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import httpx
import os
from dotenv import load_dotenv
import logging
from pathlib import Path

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="StatCampo API", version="1.0.0")

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── CONFIG ────────────────────────────────────────────────────────────────────
FOOTBALL_API_KEY  = os.getenv("FOOTBALL_API_KEY", "")
FOOTBALL_API_BASE = "https://v3.football.api-sports.io"

ALLOWED_ENDPOINTS = {
    "standings", "fixtures", "players/topscorers",
    "leagues", "teams", "players",
}

# ── PROXY FOOTBALL API ────────────────────────────────────────────────────────
@app.get("/api/football")
async def football_proxy(endpoint: str = Query(...)):
    if not FOOTBALL_API_KEY:
        raise HTTPException(status_code=500, detail="FOOTBALL_API_KEY no configurada")

    base_path = endpoint.split("?")[0]
    if base_path not in ALLOWED_ENDPOINTS:
        raise HTTPException(status_code=400, detail=f"Endpoint '{base_path}' no permitido")

    url = f"{FOOTBALL_API_BASE}/{endpoint}"
    headers = {
        "x-rapidapi-key":  FOOTBALL_API_KEY,
        "x-rapidapi-host": "v3.football.api-sports.io",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Timeout")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

# ── HEALTH CHECK ──────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "football_api_configured": bool(FOOTBALL_API_KEY),
        "version": "1.0.0"
    }

# ── SERVIR FRONTEND ───────────────────────────────────────────────────────────
STATIC_DIR = Path(__file__).parent / "static"

if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
