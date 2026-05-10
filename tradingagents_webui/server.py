"""Web server for TradingAgents WebUI.

This module imports TradingAgents from the installed package in the
TradingAgents root folder, not from a local web package.
"""

from pathlib import Path
import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="TradingAgents WebUI",
    description="Web interface for TradingAgents multi-agent trading framework",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


@app.get("/")
async def root():
    """Serve the main HTML page."""
    html_path = static_path / "index.html"
    if html_path.exists():
        return FileResponse(str(html_path))
    return {"message": "TradingAgents WebUI", "status": "running"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "tradingagents-webui", "version": "0.1.0"}


# Import and include routers from services
# These routers import TradingAgents from the system-installed package
try:
    from tradingagents_webui.routes import config, reports, analysis

    app.include_router(config.router)
    app.include_router(reports.router)
    app.include_router(analysis.router)
except ImportError as e:
    print(f"Warning: Could not import routes: {e}")
