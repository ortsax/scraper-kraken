import asyncio
import sys
from fastapi import FastAPI
from routes.api import router as api_router

app = FastAPI(title="Orsta API")
app.include_router(api_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
