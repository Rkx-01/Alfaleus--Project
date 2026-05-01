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
        self.timeout = httpx.Timeout(10.0, connect=5.0)

    async def _get(self, url: str, params: Optional[dict] = None, headers: Optional[dict] = None):
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error occurred: {e}")
            except httpx.RequestError as e:
                logger.error(f"An error occurred while requesting {e.request.url!r}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
        return None

class NewsAPICollector(BaseCollector):
    def __init__(self):
        super().__init__()
        self.api_key = settings.NEWSAPI_API_KEY
        self.base_url = "https://newsapi.org/v2/top-headlines"

    async def fetch(self, category: str = "general", country: str = "us") -> List[ArticleCreate]:
        if not self.api_key:
            logger.warning("NewsAPI API key not set. Skipping.")
            return []

        params = {
            "apiKey": self.api_key,
            "category": category,
            "country": country
        }
        
        response = await self._get(self.base_url, params=params)
        if not response:
            return []

        data = response.json()
        articles = []
        for item in data.get("articles", []):
            try:
                articles.append(ArticleCreate(
                    title=item["title"],
                    description=item.get("description") or "",
                    content=item.get("content") or item.get("description") or "",
                    url=item["url"],
                    source=item["source"]["name"],
                    published_at=datetime.fromisoformat(item["publishedAt"].replace("Z", "+00:00"))
                ))
            except (KeyError, ValueError) as e:
                logger.error(f"Error parsing NewsAPI article: {e}")
        
        return articles

class GoogleNewsRSSCollector(BaseCollector):
    def __init__(self):
        super().__init__()
        self.rss_url = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"

    async def fetch(self) -> List[ArticleCreate]:
        response = await self._get(self.rss_url)
        if not response:
            return []

        try:
            root = ET.fromstring(response.text)
            articles = []
            for item in root.findall(".//item"):
                raw_title = item.find("title").text
                url = item.find("link").text
                pub_date_str = item.find("pubDate").text
                
                # Extract real source from title (e.g. "Headline - Publisher")
                source_name = "Google RSS"
                title = raw_title
                if " - " in raw_title:
                    parts = raw_title.rsplit(" - ", 1)
                    title = parts[0].strip()
                    source_name = parts[1].strip()
                
                # Example pubDate: Sat, 25 Apr 2026 13:00:00 GMT
                try:
                    pub_date = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %Z")
                except ValueError:
                    pub_date = datetime.utcnow()

                articles.append(ArticleCreate(
                    title=title,
                    description="", # RSS often doesn't have clean description
                    content="", # RSS usually only has snippet
                    url=url,
                    source=source_name,
                    published_at=pub_date
                ))
            return articles
        except ET.ParseError as e:
            logger.error(f"Error parsing Google News RSS: {e}")
        
        return []

async def collect_all_news() -> List[ArticleCreate]:
    """
    Orchestrate fetching from all available collectors.
    """
    collectors = [
        NewsAPICollector(),
        GoogleNewsRSSCollector()
    ]
    
    all_articles = []
    for collector in collectors:
        articles = await collector.fetch()
        all_articles.extend(articles)
        logger.info(f"Collected {len(articles)} articles from {collector.__class__.__name__}")
    
    return all_articles
