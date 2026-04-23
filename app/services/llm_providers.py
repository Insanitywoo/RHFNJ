from langchain_openai import ChatOpenAI

from app.core.config import settings


def get_deepseek_chat():
    return ChatOpenAI(
        model="deepseek-chat",
        base_url="https://api.deepseek.com",
        api_key=settings.DEEPSEEK_API_KEY,
        streaming=True,
    )


async def get_chat_response(prompt: str):
    chat = get_deepseek_chat()
    async for chunk in chat.astream(prompt):
        yield chunk.content
