import logging
import traceback
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import router as api_router
from app.utils.config import settings
from app.scheduler.main import setup_scheduler
from app.db import db_manager

# Enhanced Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("API_DIAGNOSTIC")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 API WAKING UP...")
    await db_manager.connect()
    setup_scheduler()
    yield
    await db_manager.disconnect()

app = FastAPI(title="InsightMatrix API", lifespan=lifespan)

# TRIPLE-LAYER CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def diagnostic_middleware(request: Request, call_next):
    # LOG EVERY ATTEMPT
    origin = request.headers.get("origin")
    method = request.method
    path = request.url.path
    logger.info(f"🔍 REQUEST: {method} {path} from ORIGIN: {origin}")
    
    if method == "OPTIONS":
        return Response(
            status_code=204,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Max-Age": "86400",
            }
        )
    
    try:
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
    except Exception as e:
        logger.error(f"❌ REQUEST FAILED: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"status": "online", "diagnostic": "active"}
