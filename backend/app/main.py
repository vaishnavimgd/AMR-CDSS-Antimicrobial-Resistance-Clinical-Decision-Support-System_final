"""
AMR Backend — FastAPI Application Entry Point.

This is the main module that creates the FastAPI application, configures
middleware, and includes all API routers.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.upload import router as upload_router

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

# ─── Health Check ─────────────────────────────────────────────────────────────


@app.get(
    "/",
    summary="Health check",
    description="Returns a simple status to confirm the server is running.",
)
async def health_check():
    """Return server health status."""
    return {"status": "ok"}
