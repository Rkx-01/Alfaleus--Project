from fastapi import FastAPI
from app.api.v1.endpoints import router as api_router
from app.utils.config import settings

app = FastAPI(title="InsightMatrix API")
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "InsightMatrix API v1.0"}
