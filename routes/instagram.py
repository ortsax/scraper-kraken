from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from playwright.async_api import async_playwright
import asyncio
import concurrent.futures
import httpx
from .cookie import getCookie

router = APIRouter(prefix="/instagram", tags=["instagram"])


class InstagramRequest(BaseModel):
    url: str


class InstagramStoriesRequest(BaseModel):
    username: str


@router.post("/download")
async def download_instagram_media(data: InstagramRequest):
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

            return {
                "title": res_data.get("title"),
                "author": res_data.get("author"),
                "urls": [m.get("url") for m in medias if m.get("url")],
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@router.post("/stories")
async def get_instagram_stories(data: InstagramStoriesRequest):
    def run_sync():
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(execute_automation())
        finally:
            loop.close()

    async def execute_automation():
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            captured_data = {"result": None}

            async def handle_response(response):
                if (
                    "api/downloader/stories/" in response.url
                    and response.request.method == "POST"
                ):
                    try:
                        captured_data["result"] = await response.json()
                    except:
                        pass

            page.on("response", handle_response)
            await page.goto(
                "https://inflact.com/instagram-downloader/stories/",
                wait_until="domcontentloaded",
            )

            await page.fill('input[name="url"]', data.username)
            await page.click('button[type="submit"]')

            timeout = 30
            start_time = asyncio.get_event_loop().time()
            while captured_data["result"] is None:
                if asyncio.get_event_loop().time() - start_time > timeout:
                    break
                await asyncio.sleep(0.5)

            await browser.close()
            return captured_data["result"]

    try:
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            result = await loop.run_in_executor(pool, run_sync)

        if not result or result.get("status") != "success":
            raise HTTPException(status_code=400, detail="Failed to capture stories")

        stories_data = result.get("data", {})
        stories = stories_data.get("stories") if isinstance(stories_data, dict) else []

        if not isinstance(stories, list):
            stories = []

        return {
            "username": data.username,
            "count": len(stories),
            "media": [
                s.get("downloadUrl")
                for s in stories
                if isinstance(s, dict) and s.get("downloadUrl")
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
