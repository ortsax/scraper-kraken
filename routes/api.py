from fastapi import APIRouter, Query, HTTPException
from routes.cookie import getCookie

router = APIRouter()

@router.get("/cookies")
async def cookies(url: str = Query(..., description="Target URL")):
    try:
        cookie_str = await getCookie(url)
        return {"url": url, "cookies": cookie_str}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
