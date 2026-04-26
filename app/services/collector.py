import httpx
import logging
import xml.etree.ElementTree as ET
from typing import List
from app.models.news import Article

logger = logging.getLogger(__name__)

async def fetch_google_news() -> List[dict]:
    url = "https://news.google.com/rss"
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url)
            root = ET.fromstring(response.text)
            news_items = []
            for item in root.findall(".//item"):
                news_items.append({
                    "title": item.find("title").text,
                    "url": item.find("link").text,
                    "source": "Google News",
                    "published_at": item.find("pubDate").text
                })
            return news_items
        except Exception as e:
            logger.error(f"Error fetching Google News: {e}")
            return []
