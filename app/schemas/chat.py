from datetime import datetime

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    source_name: str | None = None
    session_id: int | None = None


class StreamChunk(BaseModel):
    text: str


class ChatMessageRead(BaseModel):
    id: int
    role: str
    content: str
    source_name: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatSessionRead(BaseModel):
    id: int
    title: str
    source_name: str | None
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class ChatSessionWithMessages(ChatSessionRead):
    messages: list[ChatMessageRead]


class ChatSessionCreateResponse(BaseModel):
    session: ChatSessionRead
