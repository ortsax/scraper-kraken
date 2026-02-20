import asyncio
from playwright.async_api import async_playwright
import concurrent.futures

_semaphore = asyncio.Semaphore(10)


def _run_in_proactor(url: str) -> str:
    loop = asyncio.ProactorEventLoop()
    try:
        return loop.run_until_complete(_fetch_cookies(url))
    finally:
        loop.close()


async def _fetch_cookies(url: str) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto(url, wait_until="networkidle")
        cookies = await context.cookies()
        await browser.close()

        return "; ".join(
            f"{name}={value}"
            for c in cookies
            if (name := c.get("name")) and (value := c.get("value"))
        )


async def getCookie(url: str) -> str:
    async with _semaphore:
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return await loop.run_in_executor(pool, _run_in_proactor, url)
