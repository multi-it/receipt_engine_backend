from fastapi import FastAPI
from app.config import settings
from app.api.auth import router as auth_router
from app.api.receipts import router as receipts_router

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    debug=settings.debug
)

app.include_router(auth_router)
app.include_router(receipts_router)

@app.get("/")
async def health():
    return {"status": "ok"}
