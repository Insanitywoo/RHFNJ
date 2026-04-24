from types import SimpleNamespace

from app.services import rag_service


def test_retrieve_context_uses_source_filter(monkeypatch):
    calls = {}

    class FakeVectorDB:
        def similarity_search(self, question, **kwargs):
            calls["question"] = question
            calls["kwargs"] = kwargs
            return [
                SimpleNamespace(
                    page_content="alpha",
                    metadata={"source_name": "paper.pdf", "page": 2},
                )
            ]

    monkeypatch.setattr(rag_service, "get_vector_db", lambda: FakeVectorDB())

    context = rag_service.retrieve_context("test question", source_name="paper.pdf")

    assert calls["question"] == "test question"
    assert calls["kwargs"]["filter"] == {"source_name": "paper.pdf"}
    assert "[Source: paper.pdf, Page: 2]" in context
    assert "alpha" in context
