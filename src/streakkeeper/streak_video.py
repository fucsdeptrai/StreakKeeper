import re
from urllib.parse import urlsplit

from playwright.sync_api import Error as PlaywrightError

from .tiktok import TIKTOK_OWNER_JS


FEED_URL = "https://www.tiktok.com/foryou"


def first_video_link(items) -> str:
    if not isinstance(items, list):
        return ""
    for item in items:
        if not isinstance(item, dict) or not item.get("video"):
            continue
        author = item.get("author")
        handle = author.get("uniqueId") if isinstance(author, dict) else ""
        video_id = item.get("id")
        if (isinstance(handle, str) and re.fullmatch(r"[A-Za-z0-9_.-]+", handle)
                and isinstance(video_id, str) and re.fullmatch(r"[0-9]+", video_id)):
            return f"https://www.tiktok.com/@{handle}/video/{video_id}"
    return ""


def read_feed_video(page, cancelled, *, owner="") -> str:
    first_response_link = ""

    def on_request_finished(request):
        nonlocal first_response_link
        url = urlsplit(request.url)
        if first_response_link or (url.scheme, url.netloc, url.path) != (
            "https", "www.tiktok.com", "/api/recommend/item_list/"
        ):
            return
        try:
            response = request.response()
            if response and response.ok:
                data = response.json()
                if isinstance(data, dict):
                    first_response_link = first_video_link(data.get("itemList"))
        except (ValueError, PlaywrightError):
            pass

    page.on("requestfinished", on_request_finished)
    try:
        page.goto(FEED_URL, wait_until="domcontentloaded", timeout=12000)
        for _ in range(20):
            if cancelled.is_set() or page.is_closed():
                break
            if page.url.split("?", 1)[0].rstrip("/") != FEED_URL:
                break
            try:
                actual_owner, items = page.evaluate(
                    """() => {
                        const script = document.getElementById('__UNIVERSAL_DATA_FOR_REHYDRATION__');
                        const data = JSON.parse(script?.textContent || '{}');
                        const feed = data.__DEFAULT_SCOPE__?.['webapp.updated-items'];
                        const items = Array.isArray(feed) ? feed.filter(Boolean).map(item => ({
                            id: item.id,
                            author: {uniqueId: item.author?.uniqueId},
                            video: Boolean(item.video)
                        })) : [];
                        return [(""" + TIKTOK_OWNER_JS.strip() + """), items];
                    }"""
                )
            except PlaywrightError as error:
                if "Execution context was destroyed" not in str(error):
                    raise
            else:
                if owner and actual_owner and owner != actual_owner:
                    return ""
                link = first_video_link(items) or first_response_link
                if link:
                    return link
            # Playwright dispatches browser events while waiting for a page read.
            cancelled.wait(0.4)
    finally:
        page.remove_listener("requestfinished", on_request_finished)
    return ""
