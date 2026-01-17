from fastapi import FastAPI
from app.routers import pdf

app = FastAPI(title="PDF API", version="1.0.0")

app.include_router(pdf.router, prefix="/pdf", tags=["PDF"])


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
