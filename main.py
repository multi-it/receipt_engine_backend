from fastapi import FastAPI
from app.config import settings

app = FastAPI(
    title=settings.app_name,
    description="REST API for creating and viewing receipts with authentication",
    version=settings.version,
    debug=settings.debug
)


@app.get("/")
async def health_check():
    """API health check endpoint."""
    return {
        "message": f"{settings.app_name} is running", 
        "status": "healthy", 
        "version": settings.version
    }
