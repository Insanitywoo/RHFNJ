from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

from app.services.pdf_processor import get_vector_db
from app.core.config import settings


def get_retriever():
    vector_db = get_vector_db()
    return vector_db.as_retriever(search_kwargs={"k": 10})


async def stream_rag_chat(question: str):
    retriever = get_retriever()
    docs = retriever.invoke(question)

    print(f"DEBUG: Retrieved {len(docs)} chunks")

    context_parts = []
    for doc in docs:
        source = doc.metadata.get("source", "Unknown")
        page = doc.metadata.get("page", "Unknown")
        context_parts.append(f"[Source: {source}, Page: {page}]\n{doc.page_content}")
    context = "\n\n".join(context_parts)

    system_template = """You are now a multi-document research assistant.

You have access to a library of papers.

For every statement you make, you MUST explicitly cite which paper (filename) and page number it comes from.

You MUST answer based ONLY on the provided context.

You MUST strictly use Markdown formatting.

When listing items, authors, or points, you MUST use bullet points (- ).

CRITICAL: You MUST insert a double newline after EVERY paragraph, every bullet point, and every heading to ensure proper vertical spacing.

Context: {context}

Question: {question}
"""

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate.from_template(system_template),
            HumanMessagePromptTemplate.from_template("{question}"),
        ]
    )

    llm = ChatOpenAI(
        model="deepseek-chat",
        base_url="https://api.deepseek.com",
        api_key=settings.DEEPSEEK_API_KEY,
        streaming=True,
    )

    chain = (
        {"context": lambda x: context, "question": RunnablePassthrough()} | prompt | llm
    )

    async for chunk in chain.astream(question):
        yield chunk.content
