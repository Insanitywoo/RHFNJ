from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.task import IndexingTask


def create_indexing_task(db: Session, *, document_id: int, message: str | None = None) -> IndexingTask:
    task = IndexingTask(
        document_id=document_id,
        status="queued",
        message=message or "Document queued for indexing",
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_task(db: Session, task_id: int) -> IndexingTask | None:
    return db.get(IndexingTask, task_id)


def list_tasks_for_document(db: Session, document_id: int) -> list[IndexingTask]:
    statement = (
        select(IndexingTask)
        .where(IndexingTask.document_id == document_id)
        .order_by(IndexingTask.created_at.desc(), IndexingTask.id.desc())
    )
    return list(db.scalars(statement))


def mark_task_dispatched(db: Session, task: IndexingTask, *, celery_task_id: str | None) -> IndexingTask:
    task.celery_task_id = celery_task_id
    task.message = "Task dispatched to worker"
    db.commit()
    db.refresh(task)
    return task


def mark_task_running(db: Session, task: IndexingTask) -> IndexingTask:
    task.status = "running"
    task.started_at = datetime.now(timezone.utc)
    task.error = None
    task.message = "Document indexing in progress"
    db.commit()
    db.refresh(task)
    return task


def mark_task_succeeded(db: Session, task: IndexingTask, *, chunk_count: int) -> IndexingTask:
    task.status = "succeeded"
    task.finished_at = datetime.now(timezone.utc)
    task.message = f"Document indexed successfully with {chunk_count} chunks"
    task.error = None
    db.commit()
    db.refresh(task)
    return task


def mark_task_failed(db: Session, task: IndexingTask, *, error: str) -> IndexingTask:
    task.status = "failed"
    task.finished_at = datetime.now(timezone.utc)
    task.error = error
    task.message = "Document indexing failed"
    db.commit()
    db.refresh(task)
    return task


def set_document_processing(db: Session, document: Document) -> Document:
    document.status = "processing"
    document.last_error = None
    db.commit()
    db.refresh(document)
    return document
