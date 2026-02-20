import asyncio
from playwright.async_api import async_playwright


async def getCookie(url: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(url, wait_until="networkidle")

        cookies = await context.cookies()
        await browser.close()

        return "; ".join([f"{c['name']}={c['value']}" for c in cookies])


async def main():
    cookie_str = await getCookie("https://youtube.com/")
    print(cookie_str)


if __name__ == "__main__":
    asyncio.run(main())
