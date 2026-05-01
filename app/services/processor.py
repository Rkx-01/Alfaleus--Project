import logging
import asyncio
from typing import List, Optional, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from groq import AsyncGroq
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from functools import lru_cache
from textblob import TextBlob
from app.models.news import Article
from app.utils.config import settings

logger = logging.getLogger(__name__)

client = AsyncGroq(api_key=settings.GROQ_API_KEY)

class SummarizationError(Exception):
    """Custom exception for summarization failures."""
    pass

_groq_semaphore = None

async def get_groq_semaphore():
    global _groq_semaphore
    if _groq_semaphore is None:
        _groq_semaphore = asyncio.Semaphore(5)
    return _groq_semaphore

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((SummarizationError, Exception)),
)
async def _call_groq_with_retry(prompt: str) -> str:
    """Helper to call Groq with exponential backoff for rate limits."""
    sem = await get_groq_semaphore()
    async with sem:
        try:
            response = await client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a professional news editor. You must provide exactly a 2-line summary."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=150
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Groq API call failed: {e}")
            raise SummarizationError(f"Groq call failed: {e}")

_summary_cache = {}

async def generate_summary(article_text: str) -> str:
    """
    Generate a 2-line summary of the article content.
    """
    if not article_text:
        return ""
    cache_key = hash(article_text)
    if cache_key in _summary_cache:
        return _summary_cache[cache_key]
    if not settings.GROQ_API_KEY:
        return "Summarization unavailable."
    prompt = f"Summarize the following news content into exactly 2 lines:\n\n{article_text[:4000]}"
    try:
        summary = await _call_groq_with_retry(prompt)
        lines = [line.strip() for line in summary.split('\n') if line.strip()]
        final_summary = "\n".join(lines[:2])
        _summary_cache[cache_key] = final_summary
        return final_summary
    except SummarizationError:
        return "Failed to generate summary."

def get_sentiment(text: str) -> str:
    """
    Analyze sentiment of the given text using TextBlob.
    Returns: positive / neutral / negative
    """
    if not text:
        return "neutral"
    
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    
    if polarity > 0.1:
        return "positive"
    elif polarity < -0.1:
        return "negative"
    else:
        return "neutral"

async def extract_topic_name_async(articles: List[Article]) -> Dict[str, str]:
    """
    Generate a human-readable topic name and broad category using Groq.
    """
    if not articles:
        return {"topic": "Unknown", "category": "General"}
    
    titles = "\n".join([f"- {a.title}" for a in articles])
    prompt = (
        "Analyze these news headlines and provide:\n"
        "1. A very short 2-3 word topic title.\n"
        "2. A single-word broad category. Choose the BEST fit from: Politics, Sports, Tech, Business, Health, Science, Entertainment, Crime, International.\n"
        "Avoid using 'General' unless absolutely necessary. Return ONLY the category from the list above.\n"
        "Format your response EXACTLY like this: Topic Title | Category\n\n"
        f"Headlines:\n{titles}"
    )
    try:
        response = await _call_groq_with_retry(prompt)
        if "|" in response:
            parts = response.split("|")
            return {
                "topic": parts[0].strip().replace('"', ''),
                "category": parts[1].strip().title()
            }
        return {"topic": response.strip().replace('"', ''), "category": "General"}
    except SummarizationError:
        return {"topic": articles[0].title[:100], "category": "General"}

async def cluster_articles(articles: List[Article], threshold: float = 0.22) -> List[Dict]:
    """
    Cluster articles using TF-IDF and Cosine Similarity.
    """
    if not articles:
        return []

    texts = [f"{a.title} {a.content or ''}" for a in articles]
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(texts)
    similarity_matrix = cosine_similarity(tfidf_matrix)
    
    groups = []
    visited = [False] * len(articles)
    
    for i in range(len(articles)):
        if visited[i]:
            continue
            
        current_article_group = [articles[i]]
        visited[i] = True
        
        for j in range(i + 1, len(articles)):
            if not visited[j] and similarity_matrix[i][j] >= threshold:
                current_article_group.append(articles[j])
                visited[j] = True
        
        groups.append(current_article_group)
        
    topic_tasks = [extract_topic_name_async(group) for group in groups]
    topic_data_list = await asyncio.gather(*topic_tasks, return_exceptions=True)
    
    clusters = []
    for group, data in zip(groups, topic_data_list):
        if isinstance(data, Exception):
            logger.warning(f"Topic generation failed: {data}")
            data = {"topic": group[0].title[:50] + "...", "category": "General"}
        clusters.append({
            "topic_name": data["topic"],
            "category": data["category"],
            "articles": group
        })
        
    return clusters
