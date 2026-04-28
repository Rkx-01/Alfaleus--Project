import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from app.utils.config import settings

rate_limit_db = {}

class ProductionSecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in ["/docs", "/openapi.json"]:
            return await call_next(request)
        
        api_key = request.headers.get("X-API-KEY")
        if api_key != settings.API_KEY:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
            
        client_ip = request.client.host
        now = time.time()
        record = rate_limit_db.get(client_ip, {"count": 0, "reset": now + 3600})
        if now > record["reset"]:
            record = {"count": 1, "reset": now + 3600}
        elif record["count"] >= 100:
            return JSONResponse(status_code=429, content={"detail": "Too many requests"})
        else:
            record["count"] += 1
        rate_limit_db[client_ip] = record
        
        return await call_next(request)
