"""
API Key Authentication System

Provides secure API key-based authentication for mobile and web clients.
"""

import hashlib
import secrets
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

# API Key header name
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


class APIKey(BaseModel):
    """API Key model"""

    key_hash: str
    name: str
    created_at: datetime
    last_used: Optional[datetime] = None
    rate_limit: int = 100  # requests per minute
    is_active: bool = True


class APIKeyManager:
    """Manages API keys with hashing and validation"""

    def __init__(self):
        # In production, store these in a database
        # For now, we'll use in-memory storage with example keys
        self._keys: dict[str, APIKey] = {}
        self._load_default_keys()

    def _load_default_keys(self):
        """Load default API keys from environment or config"""
        # Example: Create a default key for testing
        # In production, generate these via admin interface
        default_key = "bible_ai_dev_key_" + secrets.token_urlsafe(32)
        key_hash = self._hash_key(default_key)

        self._keys[key_hash] = APIKey(
            key_hash=key_hash,
            name="Development Key",
            created_at=datetime.utcnow(),
            rate_limit=1000,  # Higher limit for dev
        )

        # Log the default key (only in development!)
        print(f"\n{'='*60}")
        print(f"Default API Key (save this!): {default_key}")
        print(f"{'='*60}\n")

    def _hash_key(self, key: str) -> str:
        """Hash an API key using SHA-256"""
        return hashlib.sha256(key.encode()).hexdigest()

    def generate_key(self, name: str, rate_limit: int = 100) -> tuple[str, APIKey]:
        """Generate a new API key"""
        # Generate secure random key
        raw_key = f"bible_ai_{secrets.token_urlsafe(32)}"
        key_hash = self._hash_key(raw_key)

        # Create API key record
        api_key = APIKey(
            key_hash=key_hash, name=name, created_at=datetime.utcnow(), rate_limit=rate_limit
        )

        # Store (in production, save to database)
        self._keys[key_hash] = api_key

        return raw_key, api_key

    def validate_key(self, raw_key: str) -> Optional[APIKey]:
        """Validate an API key and return its record"""
        if not raw_key:
            return None

        key_hash = self._hash_key(raw_key)
        api_key = self._keys.get(key_hash)

        if not api_key or not api_key.is_active:
            return None

        # Update last used timestamp
        api_key.last_used = datetime.utcnow()

        return api_key

    def revoke_key(self, raw_key: str) -> bool:
        """Revoke an API key"""
        key_hash = self._hash_key(raw_key)
        api_key = self._keys.get(key_hash)

        if api_key:
            api_key.is_active = False
            return True

        return False


# Global API key manager instance
_api_key_manager = APIKeyManager()


async def get_api_key(api_key_header: str = Security(API_KEY_HEADER)) -> APIKey:
    """
    Dependency to validate API key from request header

    Raises:
        HTTPException: If API key is missing or invalid
    """
    if not api_key_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key. Please provide X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    api_key = _api_key_manager.validate_key(api_key_header)

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked API Key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return api_key


def get_api_key_manager() -> APIKeyManager:
    """Get the global API key manager"""
    return _api_key_manager
