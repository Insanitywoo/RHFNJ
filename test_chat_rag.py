import asyncio
from app.services.chat_service import get_chat_response_streaming


async def main():
    query = "What reinforcement learning algorithm is used in this paper?"
    print(f"Query: {query}")
    print("=" * 50)

    async for chunk in get_chat_response_streaming(query):
        print(chunk, end="", flush=True)

    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
