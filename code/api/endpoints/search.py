"""
Search Endpoints

Vector search and verse lookup endpoints.
"""

import time
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from code.api.auth import APIKey, get_api_key
from code.api.models import (
    VectorSearchRequest,
    VectorSearchResponse,
    VerseLookupRequest,
    VerseLookupResponse,
    VerseResult,
)

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/vector", response_model=VectorSearchResponse)
async def vector_search(
    request: VectorSearchRequest,
    api_key: APIKey = Depends(get_api_key),
):
    """
    Perform semantic vector search across Bible verses

    Requires valid API key. Returns verses semantically similar to query.
    """
    start_time = time.time()

    try:
        # TODO: Integrate with actual embedding search
        # For now, return mock data structure
        results = []

        # This will be replaced with actual embedding search:
        # from code.ai_training.rag_system import search_verses
        # results = search_verses(
        #     query=request.query,
        #     top_k=request.top_k,
        #     threshold=request.similarity_threshold
        # )

        # Mock response for now
        results = [
            VerseResult(
                verse_id=1,
                book_name="John",
                chapter=3,
                verse=16,
                text="For God so loved the world...",
                similarity_score=0.95,
                context=["In the beginning...", "For God so loved..."] if request.include_context else None
            )
        ]

        search_time = (time.time() - start_time) * 1000

        return VectorSearchResponse(
            query=request.query,
            results=results,
            total_results=len(results),
            search_time_ms=search_time,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )


@router.post("/verse", response_model=VerseLookupResponse)
async def lookup_verse(
    request: VerseLookupRequest,
    api_key: APIKey = Depends(get_api_key),
):
    """
    Look up a specific Bible verse by book, chapter, and verse number

    Requires valid API key.
    """
    try:
        # TODO: Integrate with database lookup
        # from code.utils.database import get_verse
        # verse = get_verse(request.book, request.chapter, request.verse)

        # Mock response
        verse = VerseResult(
            verse_id=1,
            book_name=request.book,
            chapter=request.chapter,
            verse=request.verse,
            text="Sample verse text...",
            similarity_score=1.0,
        )

        context_verses = None
        if request.include_context:
            # TODO: Get surrounding verses
            context_verses = []

        return VerseLookupResponse(verse=verse, context=context_verses)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Verse not found: {str(e)}"
        )
