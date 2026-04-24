from pathlib import Path

from app.db.session import get_session_factory
from app.models.document import Document
from app.services.task_service import create_indexing_task
from app.tasks.indexing import run_document_indexing


def test_run_document_indexing_updates_document_and_task(monkeypatch, workspace_tmp_dir, configured_env):
    pdf_path = workspace_tmp_dir / "papers" / "paper.pdf"
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.write_bytes(b"fake-pdf")

    session = get_session_factory()()
    try:
        document = Document(
            filename="paper.pdf",
            file_path=str(pdf_path),
            status="queued",
            chunk_count=0,
        )
        session.add(document)
        session.commit()
        session.refresh(document)

        task = create_indexing_task(session, document_id=document.id)
    finally:
        session.close()

    monkeypatch.setattr("app.tasks.indexing.index_pdf", lambda file_path: 9)

    result = run_document_indexing(document.id, task.id)

    assert result["chunk_count"] == 9

    verification_session = get_session_factory()()
    try:
        updated_document = verification_session.get(Document, document.id)
        updated_task = verification_session.get(type(task), task.id)
        assert updated_document.status == "ready"
        assert updated_document.chunk_count == 9
        assert updated_task.status == "succeeded"
    finally:
        verification_session.close()


def test_run_document_indexing_marks_failures(monkeypatch, workspace_tmp_dir, configured_env):
    pdf_path = workspace_tmp_dir / "papers" / "broken.pdf"
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.write_bytes(b"fake-pdf")

    session = get_session_factory()()
    try:
        document = Document(
            filename="broken.pdf",
            file_path=str(pdf_path),
            status="queued",
            chunk_count=0,
        )
        session.add(document)
        session.commit()
        session.refresh(document)

        task = create_indexing_task(session, document_id=document.id)
    finally:
        session.close()

    def fail_index(_file_path: Path) -> int:
        raise RuntimeError("embedding service unavailable")

    monkeypatch.setattr("app.tasks.indexing.index_pdf", fail_index)

    try:
        run_document_indexing(document.id, task.id)
    except RuntimeError as exc:
        assert str(exc) == "embedding service unavailable"
    else:
        raise AssertionError("Expected indexing task to fail")

    verification_session = get_session_factory()()
    try:
        updated_document = verification_session.get(Document, document.id)
        updated_task = verification_session.get(type(task), task.id)
        assert updated_document.status == "failed"
        assert updated_document.last_error == "embedding service unavailable"
        assert updated_document.chunk_count == 0
        assert updated_task.status == "failed"
        assert updated_task.error == "embedding service unavailable"
    finally:
        verification_session.close()
