"""
Bible AI Database REST API

Production-ready FastAPI application with:
- API key authentication
- Rate limiting (token bucket algorithm)
- Input validation and sanitization
- CORS support for mobile apps
- Comprehensive error handling
- OpenAPI documentation

Usage:
    uvicorn code.api.main:app --host 0.0.0.0 --port 8000 --reload

    Or using CLI:
    bible-api --host 0.0.0.0 --port 8000
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from code.api.endpoints import admin, chat, rag, search
from code.api.rate_limiter import RateLimitMiddleware

# Version
__version__ = "1.0.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown

    Startup:
    - Load embeddings into memory
    - Initialize database connections
    - Warm up models

    Shutdown:
    - Clean up resources
    - Close connections
    """
    # Startup
    print("🚀 Starting Bible AI API...")
    print(f"📖 Version: {__version__}")

    # TODO: Load embeddings
    # from code.ai_training.create_embeddings import load_embeddings
    # app.state.embeddings = load_embeddings()

    # TODO: Initialize database connection pool
    # from code.utils.database import init_db_pool
    # app.state.db_pool = init_db_pool()

    print("✅ API ready!")

    yield

    # Shutdown
    print("🛑 Shutting down API...")
    # TODO: Clean up resources
    print("✅ Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Bible AI Database API",
    description="""
    **Production-ready API for Bible AI interactions**

    Features:
    - 📚 Semantic search across 31,102 Bible verses
    - 🤖 RAG (Retrieval-Augmented Generation) for Q&A
    - 💬 Conversational AI chat interface
    - 🔐 API key authentication
    - ⚡ Rate limiting to prevent abuse
    - 📱 CORS support for mobile apps

    ## Authentication

    All endpoints (except /admin/health) require API key authentication.

    Include your API key in the `X-API-Key` header:
    ```
    X-API-Key: your_api_key_here
    ```

    ## Rate Limits

    Default: **100 requests per minute** per API key.
    Custom rate limits available for enterprise use.

    ## Getting Started

    1. Get your API key from the development team
    2. Make requests with `X-API-Key` header
    3. See example requests in the interactive docs below
    """,
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ============================================================================
# Middleware Configuration
# ============================================================================

# CORS - Allow mobile apps to access API
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining"],
)

# Rate limiting
app.add_middleware(RateLimitMiddleware)

# GZip compression for large responses
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ============================================================================
# Error Handlers
# ============================================================================


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc), "type": "validation_error"},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors"""
    # Log error (in production, use proper logging)
    print(f"❌ Unexpected error: {exc}")

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error. Please try again later.",
            "type": "server_error",
        },
    )


# ============================================================================
# Routes
# ============================================================================


@app.get("/", tags=["root"])
async def root():
    """
    API root endpoint

    Returns basic API information and links to documentation.
    """
    return {
        "name": "Bible AI Database API",
        "version": __version__,
        "status": "running",
        "documentation": {
            "interactive": "/docs",
            "redoc": "/redoc",
            "openapi_spec": "/openapi.json",
        },
        "endpoints": {
            "search": "/search/vector",
            "rag": "/rag/query",
            "chat": "/chat/message",
            "health": "/admin/health",
        },
        "authentication": "API key required (X-API-Key header)",
    }


# Include endpoint routers
app.include_router(admin.router)
app.include_router(search.router)
app.include_router(rag.router)
app.include_router(chat.router)


# ============================================================================
# CLI Entry Point
# ============================================================================


def main():
    """
    CLI entry point for running the API server

    Usage:
        bible-api
        bible-api --host 0.0.0.0 --port 8000
        bible-api --reload  # Development mode
    """
    import argparse

    import uvicorn

    parser = argparse.ArgumentParser(description="Bible AI Database API Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload (development)")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")

    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"🚀 Starting Bible AI API Server")
    print(f"{'='*60}")
    print(f"📍 Host: {args.host}")
    print(f"🔌 Port: {args.port}")
    print(f"📚 Docs: http://{args.host}:{args.port}/docs")
    print(f"{'='*60}\n")

    uvicorn.run(
        "code.api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers if not args.reload else 1,
    )


if __name__ == "__main__":
    main()
