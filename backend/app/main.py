"""
AMR Backend — FastAPI Application Entry Point.

This is the main module that creates the FastAPI application, configures
middleware, and includes all API routers.
"""

import os
import sys

# Ensure backend directory is in the python path to prevent ModuleNotFoundError
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.routes.upload import router as upload_router
from app.routes.dashboard import router as dashboard_router

# ─── Application Setup ───────────────────────────────────────────────────────

app = FastAPI(
    title="AMR Prediction Backend",
    description=(
        "Backend API for the Antimicrobial Resistance (AMR) prediction system. "
        "Accepts bacterial genome files in FASTA format, scans for resistance genes, "
        "and returns AI-powered antibiotic resistance predictions."
    ),
    version="1.0.0",
)

# ─── CORS Middleware (allow all origins during development) ───────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],         # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Register Routers ────────────────────────────────────────────────────────

app.include_router(upload_router)
app.include_router(dashboard_router)

# ─── Static Files & Dashboard frontend  ──────────────────────────────────────

# Mount frontend directory to serve CSS and JS
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
if not os.path.exists(frontend_path):
    os.makedirs(frontend_path, exist_ok=True)
app.mount("/static", StaticFiles(directory=frontend_path), name="static")

# ─── Health Check & Root ──────────────────────────────────────────────────────


@app.get(
    "/",
    summary="Serve Dashboard",
    description="Serves the main AMR-CDSS HTML dashboard.",
)
async def serve_dashboard():
    """Return the frontend dashboard."""
    dashboard_file = os.path.join(frontend_path, "amr_dashboard.html")
    if os.path.exists(dashboard_file):
        return FileResponse(dashboard_file)
    return {"status": "ok", "message": "Dashboard HTML not found"}

@app.get(
    "/health",
    summary="Health check",
)
async def health_check():
    """Return server health status."""
    return {"status": "ok"}
