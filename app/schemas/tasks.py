from datetime import datetime

from pydantic import BaseModel


class TaskRead(BaseModel):
    id: int
    document_id: int
    task_type: str
    status: str
    celery_task_id: str | None
    message: str | None
    error: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None

    model_config = {"from_attributes": True}
