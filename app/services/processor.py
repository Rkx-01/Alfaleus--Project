import httpx
from app.utils.config import settings

async def generate_summary(title: str, content: str) -> str:
    prompt = f"Summarize this news in 2-3 sentences. Title: {title}. Content: {content}"
    # ... logic
    return "Refined Summary"

async def analyze_sentiment(text: str) -> str:
    return "neutral"
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def cluster_articles_tfidf(articles, threshold=0.3):
    if not articles: return []
    texts = [a.title for a in articles]
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(texts)
    similarity = cosine_similarity(tfidf_matrix)
    # Grouping logic here...
    return []
