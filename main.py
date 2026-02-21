from fastapi import FastAPI
from routes import cookie, ytdl

app = FastAPI()

app.include_router(cookie.router)
app.include_router(ytdl.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
