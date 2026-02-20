from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, cast
import yt_dlp
import tempfile
import os
from .cookie import getCookie

router = APIRouter(prefix="/ytdl", tags=["youtube"])


class SearchQuery(BaseModel):
    query: str
    limit: int = 5


class DownloadRequest(BaseModel):
    url: str


async def get_ytdl_options(format_type: str) -> dict[str, Any]:
    cookie_content = await getCookie("https://youtube.com/", netscape=True)
    opts: dict[str, Any] = {
        "quiet": True,
        "noplaylist": True,
    }

    if cookie_content:
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".txt", encoding="utf-8"
        ) as f:
            f.write(cookie_content)
            opts["cookiefile"] = f.name

    if format_type == "audio":
        opts.update(
            {
                "format": "bestaudio/best",
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "128",
                    }
                ],
            }
        )
    else:
        # This selects the best quality that is 480p or lower
        opts["format"] = "best[height<=480]/bestvideo[height<=480]+bestaudio/best"

    return opts


def get_best_url(info: dict[str, Any]) -> str | None:
    return info.get("url") or (info.get("formats", [{}])[-1].get("url"))


@router.post("/search")
async def search_youtube(data: SearchQuery):
    ydl_opts = await get_ytdl_options("video")
    try:
        with yt_dlp.YoutubeDL(cast(Any, ydl_opts)) as ydl:
            results = cast(
                dict[str, Any],
                ydl.extract_info(f"ytsearch{data.limit}:{data.query}", download=False),
            )
            entries = results.get("entries", []) if results else []
            return [
                {
                    "title": e.get("title"),
                    "url": e.get("webpage_url"),
                    "duration": e.get("duration"),
                    "thumbnail": e.get("thumbnail"),
                }
                for e in entries
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if "cookiefile" in ydl_opts:
            os.remove(ydl_opts["cookiefile"])


@router.post("/download/video")
async def download_video(data: DownloadRequest):
    ydl_opts = await get_ytdl_options("video")
    try:
        with yt_dlp.YoutubeDL(cast(Any, ydl_opts)) as ydl:
            info = cast(dict[str, Any], ydl.extract_info(data.url, download=False))
            return {
                "title": info.get("title"),
                "download_url": get_best_url(info),
                "thumbnail": info.get("thumbnail"),
                "resolution": info.get("resolution"),
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        if "cookiefile" in ydl_opts:
            os.remove(ydl_opts["cookiefile"])


@router.post("/download/audio")
async def download_audio(data: DownloadRequest):
    ydl_opts = await get_ytdl_options("audio")
    try:
        with yt_dlp.YoutubeDL(cast(Any, ydl_opts)) as ydl:
            info = cast(dict[str, Any], ydl.extract_info(data.url, download=False))
            return {
                "title": info.get("title"),
                "download_url": get_best_url(info),
                "thumbnail": info.get("thumbnail"),
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        if "cookiefile" in ydl_opts:
            os.remove(ydl_opts["cookiefile"])


@router.post("/search-and-download")
async def search_and_download(data: SearchQuery):
    ydl_opts = await get_ytdl_options("video")
    try:
        with yt_dlp.YoutubeDL(cast(Any, ydl_opts)) as ydl:
            results = cast(
                dict[str, Any],
                ydl.extract_info(f"ytsearch1:{data.query}", download=False),
            )
            entries = results.get("entries", [])
            if not entries:
                raise HTTPException(status_code=404, detail="No results found")
            first_entry = entries[0]
            return {
                "title": first_entry.get("title"),
                "download_url": get_best_url(first_entry),
                "original_url": first_entry.get("webpage_url"),
                "thumbnail": first_entry.get("thumbnail"),
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if "cookiefile" in ydl_opts:
            os.remove(ydl_opts["cookiefile"])
