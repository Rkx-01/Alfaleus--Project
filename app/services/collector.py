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
        self.timeout = httpx.Timeout(20.0, connect=10.0)

    async def _get(self, url: str, params: Optional[dict] = None, headers: Optional[dict] = None):
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            try:
                response = await client.get(url, params=params, headers=headers)
                if response.status_code != 200:
                    logger.error(f"API Error {response.status_code} for {url}: {response.text}")
                    return None
                return response
            except Exception as e:
                logger.error(f"Network Error fetching {url}: {e}")
        return None

class NewsAPICollector(BaseCollector):
    def __init__(self):
        super().__init__()
        self.api_key = settings.NEWSAPI_API_KEY
        self.base_url = "https://newsapi.org/v2/top-headlines"

    async def fetch(self) -> List[ArticleCreate]:
        if not self.api_key: 
            logger.error("NewsAPI Key is missing!")
            return []
            
        # FIX: Added mandatory 'country' parameter
        params = {
            "apiKey": self.api_key, 
            "language": "en", 
            "country": "us", 
            "pageSize": 50
        }
        
        response = await self._get(self.base_url, params=params)
        if not response: return []
        
        articles = []
        data = response.json()
        for item in data.get("articles", []):
            try:
                if not item.get("title") or not item.get("url"): continue
                articles.append(ArticleCreate(
                    title=item["title"],
                    description=item.get("description") or "",
                    content=item.get("content") or item.get("description") or item["title"],
                    url=item["url"],
                    source=item["source"]["name"],
                    category="World",
                    published_at=datetime.fromisoformat(item["publishedAt"].replace("Z", "+00:00"))
                ))
            except Exception as e: 
                logger.warning(f"Skipping bad NewsAPI item: {e}")
                continue
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
            root = ET.fromstring(response.content)
            articles = []
            for item in root.findall(".//item"):
                try:
                    title_el = item.find("title")
                    link_el = item.find("link")
                    if title_el is None or link_el is None: continue
                    
                    title = title_el.text
                    url = link_el.text
                    desc_el = item.find("description")
                    desc = desc_el.text if desc_el is not None else ""
                    
                    articles.append(ArticleCreate(
                        title=title, description=desc, content=desc,
                        url=url, source=self.name, category=self.category,
                        published_at=datetime.utcnow()
                    ))
                except: continue
            return articles
        except Exception as e:
            logger.error(f"RSS XML Error for {self.name}: {e}")
            return []

async def collect_all_news() -> List[ArticleCreate]:
    collectors = [
        NewsAPICollector(),
        RSSCollector("BBC News", "http://feeds.bbci.co.uk/news/rss.xml", "World"),
        RSSCollector("CNN", "http://rss.cnn.com/rss/edition.rss", "World"),
        RSSCollector("TechCrunch", "https://techcrunch.com/feed/", "Technology"),
    ]
    
    all_articles = []
    for collector in collectors:
        try:
            articles = await collector.fetch()
            all_articles.extend(articles)
        except Exception as e:
            logger.error(f"Collector Failed: {e}")
    return all_articles
