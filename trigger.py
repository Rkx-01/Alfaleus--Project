import asyncio
from app.scheduler.main import run_news_digest_pipeline

if __name__ == "__main__":
    print("Triggering manual pipeline run...")
    asyncio.run(run_news_digest_pipeline())
    print("Pipeline complete!")
