from fastapi import FastAPI
from routes import cookie, ytdl, spotify, twitter, reddit, instagram

app = FastAPI()

app.include_router(cookie.router)
app.include_router(ytdl.router)
app.include_router(spotify.router)
app.include_router(twitter.router)
app.include_router(reddit.router)
app.include_router(instagram.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
