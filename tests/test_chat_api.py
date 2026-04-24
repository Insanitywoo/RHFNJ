from app.api.routes import chat as chat_route
from app.db.session import get_session_factory
from app.models.chat import ChatSession
from app.models.document import Document


def test_stream_chat_endpoint_streams_and_persists_messages(client, monkeypatch):
    session = get_session_factory()()
    try:
        session.add(
            Document(
                filename="paper.pdf",
                file_path="tests/.tmp/paper.pdf",
                status="ready",
                chunk_count=12,
            )
        )
        session.commit()
    finally:
        session.close()

    async def fake_stream_rag_chat(question: str, source_name: str | None = None):
        assert question == "hello"
        assert source_name == "paper.pdf"
        for chunk in ["part-1", "part-2"]:
            yield chunk

    monkeypatch.setattr(chat_route, "stream_rag_chat", fake_stream_rag_chat)

    response = client.post(
        "/api/v1/stream_chat",
        json={"message": "hello", "source_name": "paper.pdf"},
    )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    assert response.headers["x-session-id"].isdigit()
    assert 'data: {"text": "part-1"}' in response.text
    assert 'data: {"text": "part-2"}' in response.text
    assert "data: [DONE]" in response.text

    session_id = int(response.headers["x-session-id"])
    session_response = client.get(f"/api/v1/chat/sessions/{session_id}")
    assert session_response.status_code == 200
    payload = session_response.json()
    assert payload["id"] == session_id
    assert len(payload["messages"]) == 2
    assert payload["messages"][0]["role"] == "user"
    assert payload["messages"][1]["role"] == "assistant"
    assert payload["messages"][1]["content"] == "part-1part-2"


def test_list_chat_sessions_endpoint(client):
    create_response = client.post(
        "/api/v1/chat/sessions",
        json={"message": "session title seed", "source_name": "paper.pdf"},
    )
    assert create_response.status_code == 200

    response = client.get("/api/v1/chat/sessions")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["source_name"] == "paper.pdf"


def test_stream_chat_rejects_document_that_is_not_ready(client):
    session = get_session_factory()()
    try:
        session.add(
            Document(
                filename="queued.pdf",
                file_path="tests/.tmp/queued.pdf",
                status="queued",
                chunk_count=0,
            )
        )
        session.commit()
    finally:
        session.close()

    response = client.post(
        "/api/v1/stream_chat",
        json={"message": "hello", "source_name": "queued.pdf"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Document is not ready for chat yet"


def test_delete_chat_session_endpoint_removes_session(client):
    create_response = client.post(
        "/api/v1/chat/sessions",
        json={"message": "session title seed", "source_name": "paper.pdf"},
    )
    session_id = create_response.json()["session"]["id"]

    response = client.delete(f"/api/v1/chat/sessions/{session_id}")

    assert response.status_code == 200
    assert response.json()["message"] == "Chat session deleted successfully"

    verification_session = get_session_factory()()
    try:
        session = verification_session.get(ChatSession, session_id)
        assert session is None
    finally:
        verification_session.close()
