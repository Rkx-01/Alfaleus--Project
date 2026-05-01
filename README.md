# Multi-Source News Digest API

A production-ready FastAPI backend that collects news from multiple sources, clusters similar stories using machine learning, and generates AI-powered digests.

## Features
- **Multi-Source Collection**: Async fetching from NewsAPI and Google News RSS.
- **ML-Based Clustering**: Uses TF-IDF and Cosine Similarity to group related articles.
- **AI Summarization**: Generates synthesized digests using OpenAI GPT models.
- **Automated Pipeline**: Background processing powered by APScheduler.
- **Production-Ready**: Pydantic-based configuration, structured logging, and SQLAlchemy ORM.

## Tech Stack
- **FastAPI**: High-performance web framework.
- **SQLAlchemy**: Database ORM for PostgreSQL.
- **APScheduler**: Background task management.
- **OpenAI API**: For intelligent story summarization.
- **Scikit-learn**: For article clustering logic.
- **HTTPX**: Asynchronous HTTP client.

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configuration**:
   Copy `.env.example` to `.env` and fill in your credentials:
   ```bash
   cp .env.example .env
   ```

3. **Run the Application**:
   ```bash
   uvicorn app.main:app --reload
   ```

## API Endpoints
- `GET /api/v1/health`: Health check.
- `GET /api/v1/articles`: List all collected articles.
- `GET /api/v1/digests`: List all generated AI digests with their source articles.

## Project Structure
- `app/api/`: Route handlers.
- `app/models/`: Database schemas.
- `app/schemas/`: Data validation (Pydantic).
- `app/services/`: Core logic (collector, clusterer, summarizer).
- `app/scheduler/`: Background jobs.
- `app/utils/`: Utilities and config.
