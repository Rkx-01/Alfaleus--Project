import httpx
from app.utils.config import settings

async def generate_summary(title: str, content: str) -> str:
    prompt = f"Summarize this news in 2-3 sentences. Title: {title}. Content: {content}"
    # ... logic
    return "Refined Summary"

async def analyze_sentiment(text: str) -> str:
    return "neutral"
