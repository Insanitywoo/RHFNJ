import asyncio

from app.services.llm_providers import get_deepseek_chat


async def main():
    chat = get_deepseek_chat()
    print("Asking DeepSeek: 'What is the DFN model in battery research?'")
    print("-" * 50)

    async for chunk in chat.astream("What is the DFN model in battery research?"):
        print(chunk.content, end="", flush=True)

    print("\n" + "-" * 50)


if __name__ == "__main__":
    asyncio.run(main())
