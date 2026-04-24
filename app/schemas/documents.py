from datetime import datetime

from pydantic import BaseModel


class DocumentRead(BaseModel):
    id: int
    filename: str
    status: str
    chunk_count: int
    last_error: str | None
    created_at: datetime
    updated_at: datetime | None
    indexed_at: datetime | None

    model_config = {"from_attributes": True}


class FileUploadResponse(BaseModel):
    status: str
    filename: str
    chunks_indexed: int | None = None
    message: str
    document_id: int
    task_id: int


class DocumentListResponse(BaseModel):
    documents: list[DocumentRead]


class DocumentActionResponse(BaseModel):
    message: str
    document: DocumentRead | None = None
    task_id: int | None = None
