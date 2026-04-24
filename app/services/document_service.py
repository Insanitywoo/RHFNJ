import shutil
from datetime import datetime, timezone
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document


def get_papers_dir() -> Path:
    return settings.papers_dir_path


def get_vector_db_dir() -> Path:
    return settings.vector_db_path


def ensure_storage_dirs() -> None:
    get_papers_dir().mkdir(parents=True, exist_ok=True)
    get_vector_db_dir().mkdir(parents=True, exist_ok=True)


def sanitize_filename(filename: str) -> str:
    name = Path(filename).name.strip()
    if not name:
        raise ValueError("Filename cannot be empty")
    return name


def save_upload_file(upload: UploadFile) -> Path:
    ensure_storage_dirs()
    filename = sanitize_filename(upload.filename or "")
    destination = get_papers_dir() / filename

    with destination.open("wb") as buffer:
        shutil.copyfileobj(upload.file, buffer)

    return destination


def list_documents(db: Session) -> list[Document]:
    statement = select(Document).order_by(Document.created_at.desc(), Document.id.desc())
    return list(db.scalars(statement))


def get_document_by_filename(db: Session, filename: str) -> Document | None:
    statement = select(Document).where(Document.filename == filename)
    return db.scalar(statement)


def get_document_by_id(db: Session, document_id: int) -> Document | None:
    return db.get(Document, document_id)


def create_or_update_document_record(
    db: Session,
    *,
    filename: str,
    file_path: Path,
) -> Document:
    document = get_document_by_filename(db, filename)
    if document is None:
        document = Document(
            filename=filename,
            file_path=str(file_path),
            status="uploaded",
            chunk_count=0,
        )
        db.add(document)
    else:
        document.file_path = str(file_path)
        document.status = "uploaded"
        document.chunk_count = 0
        document.last_error = None
        document.indexed_at = None

    db.commit()
    db.refresh(document)
    return document


def mark_document_queued(db: Session, document: Document) -> Document:
    document.status = "queued"
    document.last_error = None
    db.commit()
    db.refresh(document)
    return document


def mark_document_indexed(db: Session, document: Document, *, chunk_count: int) -> Document:
    document.status = "ready"
    document.chunk_count = chunk_count
    document.last_error = None
    document.indexed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(document)
    return document


def mark_document_failed(db: Session, document: Document, *, error: str) -> Document:
    document.status = "failed"
    document.last_error = error
    db.commit()
    db.refresh(document)
    return document


def delete_document_vectors_by_source_name(source_name: str) -> None:
    from app.services.vector_store import delete_document_vectors

    delete_document_vectors(source_name=source_name)


def delete_document(db: Session, document: Document) -> None:
    from app.services.chat_service import delete_chat_sessions_for_source

    try:
        delete_document_vectors_by_source_name(document.filename)
    except ValueError:
        # Chroma raises when nothing matches. Deleting a document should still succeed.
        pass

    delete_chat_sessions_for_source(db, source_name=document.filename)

    file_path = Path(document.file_path)
    if file_path.exists():
        file_path.unlink()

    db.delete(document)
    db.commit()


def reset_document_for_reindex(db: Session, document: Document) -> Document:
    try:
        delete_document_vectors_by_source_name(document.filename)
    except ValueError:
        pass

    document.status = "queued"
    document.chunk_count = 0
    document.last_error = None
    document.indexed_at = None

    for task in list(document.tasks):
        db.delete(task)

    db.commit()
    db.refresh(document)
    return document
