from fastapi import FastAPI

app = FastAPI(
    title="Receipt Management API",
    description="REST API for creating and viewing receipts",
    version="0.1.0"
)


@app.get("/")
async def health_check():
    """API health check endpoint."""
    return {"message": "Receipt API is running", "status": "healthy"}
