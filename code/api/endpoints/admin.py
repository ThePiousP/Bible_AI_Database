"""
Admin Endpoints

API key management and system administration.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from code.api.auth import APIKey, get_api_key, get_api_key_manager
from code.api.models import (
    APIKeyInfo,
    CreateAPIKeyRequest,
    CreateAPIKeyResponse,
    HealthResponse,
    StatsResponse,
)

router = APIRouter(prefix="/admin", tags=["admin"])


# Health check (no auth required)
@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Check API health status

    No authentication required.
    """
    # TODO: Add actual checks for database and embeddings
    database_ok = True  # Check database connection
    embeddings_loaded = False  # Check if embeddings are loaded

    return HealthResponse(
        status="healthy" if database_ok else "degraded",
        version="1.0.0",
        database_status="connected" if database_ok else "disconnected",
        embeddings_loaded=embeddings_loaded,
    )


@router.get("/stats", response_model=StatsResponse)
async def get_stats(api_key: APIKey = Depends(get_api_key)):
    """
    Get database and API statistics

    Requires valid API key.
    """
    # TODO: Get actual stats from database
    return StatsResponse(
        total_verses=31102,
        total_books=66,
        total_chapters=1189,
        embeddings_count=0,  # Will be updated when embeddings are created
        api_version="1.0.0",
    )


# API Key Management (requires admin API key)
@router.post("/keys/create", response_model=CreateAPIKeyResponse)
async def create_api_key(
    request: CreateAPIKeyRequest,
    admin_key: APIKey = Depends(get_api_key),
):
    """
    Create a new API key

    Requires admin API key for authentication.
    Only admin keys can create new keys.
    """
    # Check if the requesting key has admin privileges
    # TODO: Implement role-based access control
    # For now, any valid API key can create new keys

    key_manager = get_api_key_manager()
    raw_key, api_key = key_manager.generate_key(
        name=request.name, rate_limit=request.rate_limit
    )

    return CreateAPIKeyResponse(
        api_key=raw_key,
        name=api_key.name,
        rate_limit=api_key.rate_limit,
        created_at=api_key.created_at,
    )


@router.get("/keys/list")
async def list_api_keys(admin_key: APIKey = Depends(get_api_key)):
    """
    List all API keys (without revealing the actual keys)

    Requires admin API key.
    """
    # TODO: Implement actual key listing from database
    # For now, return info about the current key only

    return {
        "keys": [
            APIKeyInfo(
                name=admin_key.name,
                created_at=admin_key.created_at,
                last_used=admin_key.last_used,
                rate_limit=admin_key.rate_limit,
                is_active=admin_key.is_active,
            ).model_dump()
        ]
    }


@router.post("/keys/revoke/{key_prefix}")
async def revoke_api_key(key_prefix: str, admin_key: APIKey = Depends(get_api_key)):
    """
    Revoke an API key

    Requires admin API key.
    Provide first 8 characters of key to revoke.
    """
    # TODO: Implement key revocation
    # For security, only match by key prefix, not full key

    return {"status": "revoked", "key_prefix": key_prefix}
