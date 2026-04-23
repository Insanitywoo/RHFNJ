from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json

from app.services.chat_service import stream_rag_chat

router = APIRouter(prefix="/api/v1", tags=["chat"])


class ChatRequest(BaseModel):
    message: str


@router.post("/stream_chat")
async def stream_chat(request: ChatRequest):
    async def event_generator():
        async for chunk in stream_rag_chat(request.message):
            yield f"data: {json.dumps({'text': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
