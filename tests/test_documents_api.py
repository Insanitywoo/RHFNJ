from app.api.routes import documents as document_route
from app.db.session import get_session_factory
from app.models.chat import ChatSession
from app.models.document import Document
from app.models.task import IndexingTask
from app.services import document_service


def test_list_documents_endpoint_returns_database_rows(client):
    session = get_session_factory()()
    try:
        session.add(
            Document(
                filename="paper-a.pdf",
                file_path="tests/.tmp/paper-a.pdf",
                status="ready",
                chunk_count=12,
            )
        )
        session.commit()
    finally:
        session.close()

    response = client.get("/api/v1/files")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["documents"]) == 1
    assert payload["documents"][0]["filename"] == "paper-a.pdf"
    assert payload["documents"][0]["status"] == "ready"


def test_upload_pdf_endpoint_persists_document(client, monkeypatch, workspace_tmp_dir, sample_pdf_bytes):
    saved_path = workspace_tmp_dir / "papers" / "paper.pdf"

    def fake_save_upload_file(upload):
        saved_path.parent.mkdir(parents=True, exist_ok=True)
        saved_path.write_bytes(sample_pdf_bytes)
        return saved_path

    monkeypatch.setattr(document_route, "enqueue_document_indexing", lambda document_id, task_id: "celery-task-123")
    monkeypatch.setattr(document_route, "save_upload_file", fake_save_upload_file)

    response = client.post(
        "/api/v1/files/upload",
        files={"file": ("paper.pdf", sample_pdf_bytes, "application/pdf")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["filename"] == "paper.pdf"
    assert payload["status"] == "queued"
    assert payload["chunks_indexed"] is None
    assert payload["document_id"] > 0
    assert payload["task_id"] > 0

    session = get_session_factory()()
    try:
        document = session.get(Document, payload["document_id"])
        task = session.get(IndexingTask, payload["task_id"])
        assert document is not None
        assert document.filename == "paper.pdf"
        assert document.status == "queued"
        assert document.chunk_count == 0
        assert task is not None
        assert task.status == "queued"
        assert task.celery_task_id == "celery-task-123"
    finally:
        session.close()

    task_response = client.get(f"/api/v1/files/tasks/{payload['task_id']}")
    assert task_response.status_code == 200
    assert task_response.json()["status"] == "queued"

    document_tasks_response = client.get(f"/api/v1/files/{payload['document_id']}/tasks")
    assert document_tasks_response.status_code == 200
    tasks_payload = document_tasks_response.json()
    assert len(tasks_payload) == 1
    assert tasks_payload[0]["id"] == payload["task_id"]
    assert tasks_payload[0]["document_id"] == payload["document_id"]
    assert tasks_payload[0]["status"] == "queued"


def test_save_upload_file_uses_basename(monkeypatch, workspace_tmp_dir):
    papers_dir = workspace_tmp_dir / "papers"
    vector_dir = workspace_tmp_dir / "vector"
    monkeypatch.setattr(document_service, "get_papers_dir", lambda: papers_dir)
    monkeypatch.setattr(document_service, "get_vector_db_dir", lambda: vector_dir)

    class DummyUpload:
        filename = "../unsafe.pdf"

        def __init__(self):
            self.file = open(__file__, "rb")

    upload = DummyUpload()
    try:
        saved_path = document_service.save_upload_file(upload)
    finally:
        upload.file.close()

    assert saved_path == papers_dir / "unsafe.pdf"
    assert saved_path.exists()


def test_download_document_endpoint_returns_pdf(client, workspace_tmp_dir):
    pdf_path = workspace_tmp_dir / "papers" / "downloadable.pdf"
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.write_bytes(b"%PDF-1.4 test payload")

    session = get_session_factory()()
    try:
        document = Document(
            filename="downloadable.pdf",
            file_path=str(pdf_path),
            status="ready",
            chunk_count=1,
        )
        session.add(document)
        session.commit()
        session.refresh(document)
        document_id = document.id
    finally:
        session.close()

    response = client.get(f"/api/v1/files/{document_id}/download")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content == b"%PDF-1.4 test payload"


def test_get_document_endpoint_returns_single_document(client):
    session = get_session_factory()()
    try:
        document = Document(
            filename="single.pdf",
            file_path="tests/.tmp/single.pdf",
            status="ready",
            chunk_count=5,
        )
        session.add(document)
        session.commit()
        session.refresh(document)
        document_id = document.id
    finally:
        session.close()

    response = client.get(f"/api/v1/files/{document_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == document_id
    assert payload["filename"] == "single.pdf"
    assert payload["status"] == "ready"


def test_reindex_document_endpoint_queues_new_task(client, monkeypatch, workspace_tmp_dir):
    pdf_path = workspace_tmp_dir / "papers" / "reindex.pdf"
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.write_bytes(b"%PDF-1.4 reindex")

    session = get_session_factory()()
    try:
        document = Document(
            filename="reindex.pdf",
            file_path=str(pdf_path),
            status="ready",
            chunk_count=11,
        )
        session.add(document)
        session.commit()
        session.refresh(document)
        document_id = document.id
    finally:
        session.close()

    monkeypatch.setattr(document_route, "enqueue_document_indexing", lambda document_id, task_id: "reindex-celery-1")
    monkeypatch.setattr(document_service, "delete_document_vectors_by_source_name", lambda source_name: None)

    response = client.post(f"/api/v1/files/{document_id}/reindex")

    assert response.status_code == 200
    payload = response.json()
    assert payload["message"] == "Document reindexing has been queued"
    assert payload["task_id"] > 0
    assert payload["document"]["status"] == "queued"
    assert payload["document"]["chunk_count"] == 0

    session = get_session_factory()()
    try:
        document = session.get(Document, document_id)
        task = session.get(IndexingTask, payload["task_id"])
        assert document is not None
        assert document.status == "queued"
        assert document.chunk_count == 0
        assert task is not None
        assert task.status == "queued"
        assert task.celery_task_id == "reindex-celery-1"
    finally:
        session.close()


def test_delete_document_endpoint_removes_document_and_file(client, monkeypatch, workspace_tmp_dir):
    pdf_path = workspace_tmp_dir / "papers" / "delete-me.pdf"
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.write_bytes(b"%PDF-1.4 delete")

    delete_calls: list[str] = []
    monkeypatch.setattr(document_service, "delete_document_vectors_by_source_name", lambda source_name: delete_calls.append(source_name))

    session = get_session_factory()()
    try:
        document = Document(
            filename="delete-me.pdf",
            file_path=str(pdf_path),
            status="failed",
            chunk_count=0,
        )
        session.add(document)
        session.add(
            ChatSession(
                title="delete-me session",
                source_name="delete-me.pdf",
            )
        )
        session.commit()
        session.refresh(document)
        document_id = document.id
    finally:
        session.close()

    response = client.delete(f"/api/v1/files/{document_id}")

    assert response.status_code == 200
    assert response.json()["message"] == "Document deleted successfully"
    assert delete_calls == ["delete-me.pdf"]
    assert not pdf_path.exists()

    session = get_session_factory()()
    try:
        assert session.get(Document, document_id) is None
        assert session.query(ChatSession).filter(ChatSession.source_name == "delete-me.pdf").count() == 0
    finally:
        session.close()
