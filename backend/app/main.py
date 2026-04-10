"""FastAPI entrypoint for the AI Call Center Assistant."""
from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes.analysis import router as analysis_router
from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.samples import router as samples_router

app = FastAPI(title="AI Call Center Assistant API")

# Comma-separated list, e.g. "http://localhost:5173,https://app.example.com"
_default_origins = "http://localhost:5173,http://127.0.0.1:5173"
_origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", _default_origins).split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(samples_router)
app.include_router(analysis_router)
