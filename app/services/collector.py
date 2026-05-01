import httpx
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Optional
from app.schemas.news import ArticleCreate
from app.utils.config import settings

logger = logging.getLogger(__name__)

class BaseCollector:
    def __init__(self):
        self.timeout = httpx.Timeout(15.0, connect=5.0)

    async def _get(self, url: str, params: Optional[dict] = None, headers: Optional[dict] = None):
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            try:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                return response
            except Exception as e:
                logger.error(f"Error fetching {url}: {e}")
        return None

class NewsAPICollector(BaseCollector):
    def __init__(self):
        super().__init__()
        self.api_key = settings.NEWSAPI_API_KEY
        self.base_url = "https://newsapi.org/v2/top-headlines"

    async def fetch(self) -> List[ArticleCreate]:
        if not self.api_key: return []
        params = {"apiKey": self.api_key, "language": "en", "pageSize": 50}
        response = await self._get(self.base_url, params=params)
        if not response: return []
        
        articles = []
        for item in response.json().get("articles", []):
            try:
                articles.append(ArticleCreate(
                    title=item["title"],
                    description=item.get("description") or "",
                    content=item.get("content") or item.get("description") or "",
                    url=item["url"],
                    source=item["source"]["name"],
                    published_at=datetime.fromisoformat(item["publishedAt"].replace("Z", "+00:00"))
                ))
            except: continue
        return articles

class RSSCollector(BaseCollector):
    def __init__(self, name: str, url: str, category: str = "World"):
        super().__init__()
        self.name = name
        self.url = url
        self.category = category

    async def fetch(self) -> List[ArticleCreate]:
        response = await self._get(self.url)
        if not response: return []
        try:
            root = ET.fromstring(response.text)
            articles = []
            for item in root.findall(".//item"):
                title = item.find("title").text
                url = item.find("link").text
                desc = item.find("description").text if item.find("description") is not None else ""
                articles.append(ArticleCreate(
                    title=title, description=desc, content=desc,
                    url=url, source=self.name, category=self.category,
                    published_at=datetime.utcnow()
                ))
            return articles
        except: return []

async def collect_all_news() -> List[ArticleCreate]:
    collectors = [
        NewsAPICollector(),
        RSSCollector("BBC News", "http://feeds.bbci.co.uk/news/rss.xml", "World"),
        RSSCollector("CNN", "http://rss.cnn.com/rss/edition.rss", "World"),
        RSSCollector("Reuters", "https://www.reutersagency.com/feed/", "Business"),
        RSSCollector("TechCrunch", "https://techcrunch.com/feed/", "Technology"),
        RSSCollector("The Verge", "https://www.theverge.com/rss/index.xml", "Technology"),
    ]
    
    all_articles = []
    for collector in collectors:
        try:
            articles = await collector.fetch()
            all_articles.extend(articles)
            logger.info(f"Collected {len(articles)} articles from {collector.name if hasattr(collector, 'name') else 'NewsAPI'}")
        except: continue
    return all_articles
