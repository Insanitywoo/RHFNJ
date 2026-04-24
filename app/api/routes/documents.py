from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.documents import DocumentActionResponse, DocumentListResponse, DocumentRead, FileUploadResponse
from app.schemas.tasks import TaskRead
from app.tasks.indexing import enqueue_document_indexing
from app.services.document_service import (
    create_or_update_document_record,
    delete_document,
    get_document_by_id,
    list_documents,
    mark_document_queued,
    reset_document_for_reindex,
    save_upload_file,
)
from app.services.task_service import (
    create_indexing_task,
    get_task,
    list_tasks_for_document,
    mark_task_dispatched,
)


router = APIRouter()


@router.get("", response_model=DocumentListResponse)
async def get_documents(db: Session = Depends(get_db)) -> DocumentListResponse:
    return DocumentListResponse(documents=list_documents(db))


@router.get("/{document_id}", response_model=DocumentRead)
async def get_document(document_id: int, db: Session = Depends(get_db)) -> DocumentRead:
    document = get_document_by_id(db, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return DocumentRead.model_validate(document)


@router.get("/{document_id}/tasks", response_model=list[TaskRead])
async def get_document_tasks(document_id: int, db: Session = Depends(get_db)) -> list[TaskRead]:
    document = get_document_by_id(db, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return [TaskRead.model_validate(task) for task in list_tasks_for_document(db, document_id)]


@router.get("/{document_id}/download")
async def download_document(document_id: int, db: Session = Depends(get_db)) -> FileResponse:
    document = get_document_by_id(db, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    file_path = Path(document.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document file not found")

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=document.filename,
    )


@router.get("/tasks/{task_id}", response_model=TaskRead)
async def get_task_status(task_id: int, db: Session = Depends(get_db)) -> TaskRead:
    task = get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return TaskRead.model_validate(task)


@router.post("/{document_id}/reindex", response_model=DocumentActionResponse)
async def reindex_document(document_id: int, db: Session = Depends(get_db)) -> DocumentActionResponse:
    document = get_document_by_id(db, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    file_path = Path(document.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document file not found")

    document = reset_document_for_reindex(db, document)
    task = create_indexing_task(
        db,
        document_id=document.id,
        message="Document queued for reindexing",
    )
    celery_task_id = enqueue_document_indexing(document.id, task.id)
    mark_task_dispatched(db, task, celery_task_id=celery_task_id)

    return DocumentActionResponse(
        message="Document reindexing has been queued",
        document=DocumentRead.model_validate(document),
        task_id=task.id,
    )


@router.delete("/{document_id}", response_model=DocumentActionResponse)
async def delete_document_endpoint(document_id: int, db: Session = Depends(get_db)) -> DocumentActionResponse:
    document = get_document_by_id(db, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    delete_document(db, document)
    return DocumentActionResponse(message="Document deleted successfully")


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> FileUploadResponse:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed",
        )

    saved_path = save_upload_file(file)
    document = create_or_update_document_record(
        db,
        filename=saved_path.name,
        file_path=saved_path,
    )
    document = mark_document_queued(db, document)
    task = create_indexing_task(
        db,
        document_id=document.id,
        message="Document uploaded and queued for indexing",
    )
    celery_task_id = enqueue_document_indexing(document.id, task.id)
    mark_task_dispatched(db, task, celery_task_id=celery_task_id)

    return FileUploadResponse(
        status="queued",
        filename=saved_path.name,
        chunks_indexed=None,
        message="File uploaded and indexing task created",
        document_id=document.id,
        task_id=task.id,
    )
