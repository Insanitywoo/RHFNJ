from pathlib import Path

from app.core.celery_app import celery_app
from app.db.session import get_session_factory
from app.models.document import Document
from app.services.document_service import mark_document_failed, mark_document_indexed
from app.services.indexing_service import index_pdf
from app.services.task_service import (
    get_task,
    mark_task_failed,
    mark_task_running,
    mark_task_succeeded,
    set_document_processing,
)


@celery_app.task(name="app.tasks.indexing.run_document_indexing")
def run_document_indexing(document_id: int, task_id: int) -> dict[str, int]:
    session_factory = get_session_factory()
    db = session_factory()
    try:
        document = db.get(Document, document_id)
        task = get_task(db, task_id)
        if document is None or task is None:
            raise ValueError("Document or indexing task not found")

        set_document_processing(db, document)
        mark_task_running(db, task)

        chunk_count = index_pdf(Path(document.file_path))

        mark_document_indexed(db, document, chunk_count=chunk_count)
        mark_task_succeeded(db, task, chunk_count=chunk_count)
        return {"document_id": document_id, "task_id": task_id, "chunk_count": chunk_count}
    except Exception as exc:
        document = db.get(Document, document_id)
        task = get_task(db, task_id)
        if document is not None:
            mark_document_failed(db, document, error=str(exc))
        if task is not None:
            mark_task_failed(db, task, error=str(exc))
        raise
    finally:
        db.close()


def enqueue_document_indexing(document_id: int, task_id: int) -> str:
    result = run_document_indexing.delay(document_id, task_id)
    return str(result.id)
