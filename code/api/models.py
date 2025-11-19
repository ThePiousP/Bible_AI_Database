"""
API Request/Response Models

Pydantic models for input validation and response serialization.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Search & Embeddings Models
# ============================================================================


class VectorSearchRequest(BaseModel):
    """Request for semantic vector search"""

    query: str = Field(..., min_length=1, max_length=500, description="Search query text")
    top_k: int = Field(10, ge=1, le=100, description="Number of results to return")
    similarity_threshold: float = Field(
        0.3, ge=0.0, le=1.0, description="Minimum similarity score (0-1)"
    )
    include_context: bool = Field(
        True, description="Include surrounding verses as context"
    )
    filters: Optional[dict] = Field(
        None, description="Optional filters (book, testament, etc.)"
    )

    @field_validator("query")
    @classmethod
    def sanitize_query(cls, v: str) -> str:
        """Sanitize query input"""
        # Remove potential SQL injection attempts
        dangerous_chars = [";", "--", "/*", "*/", "xp_", "sp_", "exec", "execute"]
        query_lower = v.lower()
        for char in dangerous_chars:
            if char in query_lower:
                raise ValueError(f"Invalid character sequence in query: {char}")
        return v.strip()


class VerseResult(BaseModel):
    """Single verse search result"""

    verse_id: int
    book_name: str
    chapter: int
    verse: int
    text: str
    similarity_score: float
    context: Optional[List[str]] = None  # Surrounding verses


class VectorSearchResponse(BaseModel):
    """Response for vector search"""

    query: str
    results: List[VerseResult]
    total_results: int
    search_time_ms: float


# ============================================================================
# RAG Models
# ============================================================================


class RAGRequest(BaseModel):
    """Request for RAG (Retrieval-Augmented Generation) query"""

    question: str = Field(
        ..., min_length=5, max_length=1000, description="Question about the Bible"
    )
    top_k: int = Field(10, ge=1, le=50, description="Number of verses to retrieve")
    similarity_threshold: float = Field(0.3, ge=0.0, le=1.0)
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="LLM temperature")
    max_tokens: int = Field(500, ge=50, le=2000, description="Maximum response tokens")

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        """Validate and sanitize question"""
        if not v.strip():
            raise ValueError("Question cannot be empty")
        # Remove potential prompt injection
        if any(injection in v.lower() for injection in ["ignore previous", "system:", "assistant:"]):
            raise ValueError("Potential prompt injection detected")
        return v.strip()


class RAGResponse(BaseModel):
    """Response for RAG query"""

    question: str
    answer: str
    relevant_verses: List[VerseResult]
    confidence_score: Optional[float] = None
    processing_time_ms: float


# ============================================================================
# Chat Models
# ============================================================================


class ChatMessage(BaseModel):
    """Single chat message"""

    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str = Field(..., min_length=1, max_length=2000)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatRequest(BaseModel):
    """Request for chat conversation"""

    messages: List[ChatMessage] = Field(..., min_items=1, max_items=50)
    use_rag: bool = Field(
        True, description="Use RAG to ground responses in Bible text"
    )
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(500, ge=50, le=2000)

    @field_validator("messages")
    @classmethod
    def validate_messages(cls, v: List[ChatMessage]) -> List[ChatMessage]:
        """Ensure last message is from user"""
        if not v:
            raise ValueError("At least one message required")
        if v[-1].role != "user":
            raise ValueError("Last message must be from user")
        return v


class ChatResponse(BaseModel):
    """Response for chat conversation"""

    message: ChatMessage
    relevant_verses: Optional[List[VerseResult]] = None
    processing_time_ms: float


# ============================================================================
# Verse Lookup Models
# ============================================================================


class VerseLookupRequest(BaseModel):
    """Request for specific verse lookup"""

    book: str = Field(..., min_length=2, max_length=50)
    chapter: int = Field(..., ge=1, le=150)
    verse: int = Field(..., ge=1, le=176)  # Longest chapter is Psalm 119
    include_context: bool = Field(False, description="Include surrounding verses")


class VerseLookupResponse(BaseModel):
    """Response for verse lookup"""

    verse: VerseResult
    context: Optional[List[VerseResult]] = None


# ============================================================================
# Statistics & Health Models
# ============================================================================


class HealthResponse(BaseModel):
    """API health check response"""

    status: str
    version: str
    database_status: str
    embeddings_loaded: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StatsResponse(BaseModel):
    """Database statistics"""

    total_verses: int
    total_books: int
    total_chapters: int
    embeddings_count: int
    api_version: str


# ============================================================================
# Admin Models (API Key Management)
# ============================================================================


class CreateAPIKeyRequest(BaseModel):
    """Request to create new API key"""

    name: str = Field(..., min_length=3, max_length=100)
    rate_limit: int = Field(100, ge=10, le=10000, description="Requests per minute")


class CreateAPIKeyResponse(BaseModel):
    """Response with new API key"""

    api_key: str = Field(..., description="Save this! It won't be shown again.")
    name: str
    rate_limit: int
    created_at: datetime


class APIKeyInfo(BaseModel):
    """API key information (without the actual key)"""

    name: str
    created_at: datetime
    last_used: Optional[datetime]
    rate_limit: int
    is_active: bool
