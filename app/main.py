import logging
import traceback
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from app.api.v1.endpoints import router as api_router
from app.utils.config import settings
from app.db import db_manager
from app.scheduler.main import setup_scheduler

# Simple, direct logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PRODUCTION_STABLE")

app = FastAPI(title="InsightMatrix Stable API")

# 1. ONE-TIME STARTUP (Simple and safe)
@app.on_event("startup")
async def startup_event():
    logger.info("⚡️ SYSTEM STARTING...")
    try:
        await db_manager.connect()
        setup_scheduler()
    except Exception as e:
        logger.error(f"STARTUP ERROR: {e}")

# 2. FAIL-SAFE CORS MIDDLEWARE (The "Unbreakable" version)
@app.middleware("http")
async def universal_cors_middleware(request: Request, call_next):
    # Handle Preflight (OPTIONS)
    if request.method == "OPTIONS":
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
        # Try to get the response
        response = await call_next(request)
    except Exception as e:
        # If the backend crashes, still send CORS headers so the browser sees the error
        logger.error(f"CRASH DETECTED: {str(e)}\n{traceback.format_exc()}")
        response = JSONResponse(
            status_code=500,
            content={"error": "Backend Error", "detail": str(e)}
        )
    
    # FORCE CORS HEADERS ON EVERY SINGLE RESPONSE
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# 3. Routes
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"status": "online", "mode": "failsafe"}
