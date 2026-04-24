from langchain_openai import ChatOpenAI

from app.core.config import settings


def get_chat_model() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.DEEPSEEK_CHAT_MODEL,
        base_url=settings.DEEPSEEK_BASE_URL,
        api_key=settings.DEEPSEEK_API_KEY,
        streaming=True,
    )
