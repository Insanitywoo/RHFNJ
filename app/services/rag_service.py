from langchain_core.prompts import ChatPromptTemplate

from app.core.config import settings
from app.services.llm_service import get_chat_model
from app.services.vector_store import get_vector_db


RAG_SYSTEM_PROMPT = """You are a research assistant for battery and engineering papers.

Use only the provided context to answer the question.

Every factual statement must cite the source filename and page number.

Always use Markdown.

If the answer is not in the context, say that the context does not contain enough information.

Context:
{context}
"""


def retrieve_context(question: str, source_name: str | None = None) -> str:
    vector_db = get_vector_db()
    search_kwargs: dict[str, object] = {"k": settings.RETRIEVAL_TOP_K}
    if source_name:
        search_kwargs["filter"] = {"source_name": source_name}

    docs = vector_db.similarity_search(question, **search_kwargs)

    context_parts: list[str] = []
    for doc in docs:
        source = doc.metadata.get("source_name", "Unknown")
        page = doc.metadata.get("page", "Unknown")
        context_parts.append(f"[Source: {source}, Page: {page}]\n{doc.page_content}")

    return "\n\n".join(context_parts)


async def stream_rag_chat(question: str, source_name: str | None = None):
    context = retrieve_context(question, source_name=source_name)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", RAG_SYSTEM_PROMPT),
            ("human", "Question: {question}"),
        ]
    )

    chain = prompt | get_chat_model()
    async for chunk in chain.astream({"context": context, "question": question}):
        if chunk.content:
            yield chunk.content
