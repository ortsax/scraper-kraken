from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import urllib.parse
from .cookie import getCookie
from .ytdl import get_ytdl_options, get_best_url  # Import existing YTDL logic
import yt_dlp
from typing import Any, cast
import os

router = APIRouter(prefix="/spotify", tags=["spotify"])


class SpotifyRequest(BaseModel):
    spotify_url: str


@router.post("/search")
async def search_spotify(data: SpotifyRequest):
    cookie_content = await getCookie("https://spotmate.online/en1", netscape=False)

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Referer": "https://spotmate.online/en1",
        "Origin": "https://spotmate.online",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    if cookie_content:
        headers["Cookie"] = cookie_content
        try:
            parts = cookie_content.split("XSRF-TOKEN=")
            if len(parts) > 1:
                token = parts[1].split(";")[0]
                headers["X-XSRF-TOKEN"] = urllib.parse.unquote(token)
        except Exception:
            pass

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://spotmate.online/getTrackData",
                json={"spotify_url": data.spotify_url},
                headers=headers,
                timeout=15.0,
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code, detail="Spotmate API error"
                )

            return response.json()

        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Request failed: {str(exc)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/download")
async def download_spotify_track(data: SpotifyRequest):
    spotify_data = await search_spotify(data)
    title = spotify_data.get("name")
    artist = spotify_data.get("artists", [{}])[0].get("name", "")
    search_query = f"{title} {artist} official audio"

    # 2. Search and Extract from YouTube
    ydl_opts = await get_ytdl_options("audio")
    try:
        with yt_dlp.YoutubeDL(cast(Any, ydl_opts)) as ydl:
            results = cast(
                dict[str, Any],
                ydl.extract_info(f"ytsearch1:{search_query}", download=False),
            )
            entries = results.get("entries", [])
            if not entries:
                raise HTTPException(
                    status_code=404, detail="No matching audio found on YouTube"
                )

            first_entry = entries[0]
            return {
                "spotify_title": title,
                "spotify_artist": artist,
                "youtube_title": first_entry.get("title"),
                "download_url": get_best_url(first_entry),
                "thumbnail": spotify_data.get("album", {})
                .get("images", [{}])[0]
                .get("url"),
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if "cookiefile" in ydl_opts:
            if os.path.exists(ydl_opts["cookiefile"]):
                os.remove(ydl_opts["cookiefile"])
