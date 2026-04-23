import asyncio
from app.services.chat_service import stream_rag_chat


async def main():
    query = "What is the methodology used in this paper?"
    print(f"Query: {query}")
    print("=" * 50)

    async for chunk in stream_rag_chat(query):
        print(chunk, end="", flush=True)

    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
