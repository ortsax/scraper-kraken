from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
from .cookie import getCookie

router = APIRouter(prefix="/reddit", tags=["reddit"])


class RedditRequest(BaseModel):
    url: str


@router.post("/download")
async def download_reddit_video(data: RedditRequest):
    cookie_content = await getCookie("https://downr.org/", netscape=False)

    headers = {
        "Content-Type": "application/json",
        "Referer": "https://downr.org/",
        "Origin": "https://downr.org/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    if cookie_content:
        headers["Cookie"] = cookie_content

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://downr.org/.netlify/functions/nyt",
                json={"url": data.url},
                headers=headers,
                timeout=15.0,
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code, detail="Downr API error"
                )

            res_data = response.json()
            medias = res_data.get("medias", [])

            if not medias:
                raise HTTPException(status_code=404, detail="No media found")

            results = []
            for media in medias:
                results.append(
                    {
                        "url": media.get("url"),
                        "type": media.get("type"),
                        "quality": media.get("quality"),
                    }
                )

            return {
                "title": res_data.get("title"),
                "author": res_data.get("author"),
                "media": results,
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
