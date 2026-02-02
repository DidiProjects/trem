import hashlib
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pathlib import Path
from app.routers import pdfRoute, videoRoute, audioRoute
from app.config import get_settings

static_dir = Path(__file__).parent / "static"


def get_file_hash(filepath: Path) -> str:
    if filepath.exists():
        content = filepath.read_bytes()
        return hashlib.md5(content).hexdigest()[:8]
    return ""


static_hashes = {
    "style.css": get_file_hash(static_dir / "style.css"),
    "script.js": get_file_hash(static_dir / "script.js"),
}


class CacheControlMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/static/"):
            if "?" in str(request.url):
                response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
            else:
                response.headers["Cache-Control"] = "public, max-age=3600"
        return response


app = FastAPI(title="API Tools", version="1.0.0")
app.add_middleware(CacheControlMiddleware)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.include_router(pdfRoute.router, prefix="/pdf", tags=["PDF"])
app.include_router(videoRoute.router, prefix="/movie", tags=["Movies"])
app.include_router(audioRoute.router, prefix="/audio", tags=["Audio"])


@app.get("/")
async def root():
    html_content = (static_dir / "index.html").read_text(encoding="utf-8")
    html_content = html_content.replace(
        'href="/static/style.css"',
        f'href="/static/style.css?v={static_hashes["style.css"]}"'
    )
    html_content = html_content.replace(
        'src="/static/script.js"',
        f'src="/static/script.js?v={static_hashes["script.js"]}"'
    )
    return HTMLResponse(content=html_content)


@app.get("/config")
async def get_config():
    settings = get_settings()
    return {"api_url": settings.API_URL}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
