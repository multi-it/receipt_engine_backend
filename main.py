from fastapi import FastAPI
from app.config import settings

app = FastAPI(title=settings.app_name, version=settings.version)

@app.get("/")
async def health():
    return {"status": "ok"}
