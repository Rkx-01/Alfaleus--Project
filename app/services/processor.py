import httpx
import logging
from app.utils.config import settings

logger = logging.getLogger(__name__)

async def generate_summary(title: str, content: str) -> str:
    if not settings.GROQ_API_KEY:
        return f"Summary for {title}"
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
    payload = {
        "model": "llama3-70b-8192",
        "messages": [{"role": "user", "content": f"Summarize: {title}\n{content}"}]
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers, json=payload)
        return resp.json()["choices"][0]["message"]["content"]

async def analyze_sentiment(text: str) -> str:
    # Simple rule-based sentiment for now
    positive_words = ["success", "gain", "growth", "breakthrough", "happy"]
    negative_words = ["loss", "crisis", "fail", "drop", "warning"]
    
    score = 0
    words = text.lower().split()
    for w in words:
        if w in positive_words: score += 1
        if w in negative_words: score -= 1
    
    if score > 0: return "positive"
    if score < 0: return "negative"
    return "neutral"
