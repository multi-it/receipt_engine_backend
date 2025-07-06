from fastapi import FastAPI
from app.api.auth import router as auth_router
from app.api.receipts import router as receipts_router
from app.api.public import router as public_router

app = FastAPI(title="Receipt Management API", version="1.0.0")

app.include_router(auth_router)
app.include_router(receipts_router)
app.include_router(public_router)

@app.get("/")
async def health_check():
    return {"status": "ok"}
