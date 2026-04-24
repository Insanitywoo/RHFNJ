import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.chat import (
    ChatRequest,
    ChatSessionCreateResponse,
    ChatSessionRead,
    ChatSessionWithMessages,
)
from app.services.chat_service import (
    create_chat_session,
    delete_chat_session,
    get_chat_session,
    list_chat_session_messages,
    list_chat_sessions,
    save_chat_message,
)
from app.services.document_service import get_document_by_filename
from app.services.rag_service import stream_rag_chat


router = APIRouter()


@router.post("/chat/sessions", response_model=ChatSessionCreateResponse)
async def create_session(
    request: ChatRequest,
    db: Session = Depends(get_db),
) -> ChatSessionCreateResponse:
    session = create_chat_session(
        db,
        source_name=request.source_name,
        title=request.message[:80].strip() or None,
    )
    return ChatSessionCreateResponse(session=ChatSessionRead.model_validate(session))


@router.get("/chat/sessions", response_model=list[ChatSessionRead])
async def get_sessions(db: Session = Depends(get_db)) -> list[ChatSessionRead]:
    return [ChatSessionRead.model_validate(item) for item in list_chat_sessions(db)]


@router.get("/chat/sessions/{session_id}", response_model=ChatSessionWithMessages)
async def get_session_messages(
    session_id: int,
    db: Session = Depends(get_db),
) -> ChatSessionWithMessages:
    session = list_chat_session_messages(db, session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
    )
    return ChatSessionWithMessages.model_validate(session)


@router.delete("/chat/sessions/{session_id}")
async def remove_session(
    session_id: int,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    session = get_chat_session(db, session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )
    delete_chat_session(db, session)
    return {"message": "Chat session deleted successfully"}


@router.post("/stream_chat")
async def stream_chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    if request.source_name:
        document = get_document_by_filename(db, request.source_name)
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found",
            )
        if document.status != "ready":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Document is not ready for chat yet",
            )

    chat_session = (
        get_chat_session(db, request.session_id)
        if request.session_id is not None
        else None
    )
    if request.session_id is not None and chat_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )
    if chat_session is None:
        chat_session = create_chat_session(
            db,
            source_name=request.source_name,
            title=request.message[:80].strip() or None,
        )

    save_chat_message(
        db,
        session_id=chat_session.id,
        role="user",
        content=request.message,
        source_name=request.source_name,
    )

    async def event_generator():
        assistant_parts: list[str] = []
        async for chunk in stream_rag_chat(
            question=request.message,
            source_name=request.source_name,
        ):
            assistant_parts.append(chunk)
            yield f"data: {json.dumps({'text': chunk})}\n\n"
        save_chat_message(
            db,
            session_id=chat_session.id,
            role="assistant",
            content="".join(assistant_parts),
            source_name=request.source_name,
        )
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"X-Session-Id": str(chat_session.id)},
    )
