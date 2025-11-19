"""
Chat Endpoints

Conversational AI endpoints for Bible discussion.
"""

import time
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from code.api.auth import APIKey, get_api_key
from code.api.models import ChatMessage, ChatRequest, ChatResponse, VerseResult

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message", response_model=ChatResponse)
async def chat_message(
    request: ChatRequest,
    api_key: APIKey = Depends(get_api_key),
):
    """
    Send a message in a chat conversation about the Bible

    Maintains conversation context and optionally grounds responses in Bible text using RAG.

    Requires valid API key.
    """
    start_time = time.time()

    try:
        # Get the last user message
        last_message = request.messages[-1]

        # TODO: Integrate with actual chat system
        # from code.ai_training.chat_interface import generate_response
        # response_text, verses = generate_response(
        #     messages=request.messages,
        #     use_rag=request.use_rag,
        #     temperature=request.temperature,
        #     max_tokens=request.max_tokens
        # )

        # Mock response
        response_text = (
            f"Thank you for your question: '{last_message.content}'. "
            "Based on Scripture, I can help you understand this topic better."
        )

        relevant_verses = None
        if request.use_rag:
            relevant_verses = [
                VerseResult(
                    verse_id=1,
                    book_name="John",
                    chapter=1,
                    verse=1,
                    text="In the beginning was the Word...",
                    similarity_score=0.88,
                )
            ]

        assistant_message = ChatMessage(
            role="assistant",
            content=response_text,
            timestamp=datetime.utcnow(),
        )

        processing_time = (time.time() - start_time) * 1000

        return ChatResponse(
            message=assistant_message,
            relevant_verses=relevant_verses,
            processing_time_ms=processing_time,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {str(e)}",
        )


@router.get("/demo")
async def chat_demo(api_key: APIKey = Depends(get_api_key)):
    """
    Get demo conversation examples

    Requires valid API key.
    """
    example_conversation = [
        ChatMessage(role="user", content="Tell me about the creation story"),
        ChatMessage(
            role="assistant",
            content="The creation story is found in Genesis 1-2. In the beginning, God created the heavens and the earth...",
        ),
        ChatMessage(role="user", content="How many days did it take?"),
        ChatMessage(
            role="assistant",
            content="According to Genesis 1, God created the world in six days and rested on the seventh day...",
        ),
    ]

    return {
        "example_conversation": [msg.model_dump() for msg in example_conversation],
        "note": "Use POST /chat/message to start your own conversation",
    }
