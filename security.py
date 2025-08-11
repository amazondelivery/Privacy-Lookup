from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

import time
from collections import defaultdict

#prevents DDoS
class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients = defaultdict(list)
    
    async def dispatch(self, request:Request, call_next):
        client_ip = request.client.host
        now = time.time()

        self.clients[client_ip] = [
            req_time for req_time in self.clients[client_ip]
            if now - req_time < self.period
        ]

        if len(self.clients[client_ip]) >= self.calls:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        self.clients[client_ip].append(now)
        response = await call_next(request)

        return response
    
def setup_security(app: FastAPI):
    app.add_middleware(RateLimitMiddleware, calls=100, period=60)

    #CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://your-app-name.onrender.com",  # Your Render URL
            "http://localhost:8000"  # For local development
        ],
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["*"]
    )

    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[
            "privacy-lookup.onrender.com",
            "*.onrender.com",
            "localhost",
            "127.0.0.1",
            "0.0.0.0:8000",
            "localhost:8000",
            "127.0.0.1:8000"
        ]
    )

    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'"
        return response