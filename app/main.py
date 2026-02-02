from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from app.routers import pdfRoute, videoRoute
from app.config import get_settings

app = FastAPI(title="PDF API", version="1.0.0")

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.include_router(pdfRoute.router, prefix="/pdf", tags=["PDF"])
app.include_router(videoRoute.router, prefix="/movie", tags=["Movies"])


@app.get("/")
async def root():
    return FileResponse(static_dir / "index.html")


@app.get("/config")
async def get_config():
    settings = get_settings()
    return {"api_url": settings.API_URL}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
