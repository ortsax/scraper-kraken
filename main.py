from fastapi import FastAPI
from routes import api, ytdl

app = FastAPI()

app.include_router(api.router)
app.include_router(ytdl.router)
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
