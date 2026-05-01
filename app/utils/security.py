import time
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.config import settings

# In-memory rate limiting storage (In production, use Redis)
rate_limit_records = {}

class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. API Key Authentication
        api_key = request.headers.get("X-API-KEY")
        if api_key != settings.API_KEY:
            return HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API Key"
            ) # Note: Middleware needs to return a Response, not raise an error usually

        # 2. Rate Limiting (100 requests per hour per IP)
        client_ip = request.client.host
        current_time = time.time()
        hour_in_seconds = 3600
        
        if client_ip not in rate_limit_records:
            rate_limit_records[client_ip] = {"count": 1, "reset_at": current_time + hour_in_seconds}
        else:
            record = rate_limit_records[client_ip]
            if current_time > record["reset_at"]:
                # Reset if hour has passed
                rate_limit_records[client_ip] = {"count": 1, "reset_at": current_time + hour_in_seconds}
            else:
                if record["count"] >= 100:
                    return HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Rate limit exceeded. Max 100 requests per hour."
                    )
                record["count"] += 1

        response = await call_next(request)
        return response

# Note: Above middleware returns HTTPException which isn't ideal for BaseHTTPMiddleware.
# Refactoring to return a proper JSONResponse for production robustness.
from fastapi.responses import JSONResponse

class ProductionSecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip security for root, docs, and all trigger/pulse paths
        path = request.url.path.rstrip("/")
        if path in ["", "/docs", "/openapi.json", "/redoc", "/trigger-now", "/pulse-check"] or request.method == "OPTIONS":
            return await call_next(request)

        # 1. API Key Check
        api_key = request.headers.get("X-API-KEY")
        if api_key != settings.API_KEY:
            return JSONResponse(
                status_code=401,
                content={"detail": "Unauthorized: Invalid API Key"}
            )

        # 2. Rate Limit Check
        client_ip = request.client.host
        now = time.time()
        
        record = rate_limit_records.get(client_ip)
        if not record or now > record["reset_at"]:
            rate_limit_records[client_ip] = {"count": 1, "reset_at": now + 3600}
        elif record["count"] >= 1000:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded (1000 req/hour)"}
            )
        else:
            record["count"] += 1

        return await call_next(request)
