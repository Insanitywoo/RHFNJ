from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.chat import ChatMessage, ChatSession


def create_chat_session(
    db: Session,
    *,
    source_name: str | None = None,
    title: str | None = None,
) -> ChatSession:
    session = ChatSession(
        title=title or (source_name or "New Chat"),
        source_name=source_name,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_chat_session(db: Session, session_id: int) -> ChatSession | None:
    statement = select(ChatSession).where(ChatSession.id == session_id)
    return db.scalar(statement)


def list_chat_sessions(db: Session) -> list[ChatSession]:
    statement = select(ChatSession).order_by(ChatSession.updated_at.desc(), ChatSession.id.desc())
    return list(db.scalars(statement))


def delete_chat_session(db: Session, session: ChatSession) -> None:
    db.delete(session)
    db.commit()


def delete_chat_sessions_for_source(db: Session, *, source_name: str) -> int:
    statement = select(ChatSession).where(ChatSession.source_name == source_name)
    sessions = list(db.scalars(statement))
    count = len(sessions)
    for session in sessions:
        db.delete(session)
    db.commit()
    return count


def list_chat_session_messages(db: Session, session_id: int) -> ChatSession | None:
    statement = (
        select(ChatSession)
        .options(selectinload(ChatSession.messages))
        .where(ChatSession.id == session_id)
    )
    return db.scalar(statement)


def save_chat_message(
    db: Session,
    *,
    session_id: int,
    role: str,
    content: str,
    source_name: str | None = None,
) -> ChatMessage:
    message = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
        source_name=source_name,
    )
    db.add(message)

    session = get_chat_session(db, session_id)
    if session is not None:
        if role == "user" and session.title in {"New Chat", session.source_name or "", ""}:
            session.title = content.strip()[:80] or session.title
        if source_name and not session.source_name:
            session.source_name = source_name

    db.commit()
    db.refresh(message)
    return message
