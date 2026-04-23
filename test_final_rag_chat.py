import asyncio
from app.services.chat_service import stream_rag_chat


async def main():
    query = "Explain the battery fast charging optimization approach described in this paper"
    print(f"Query: {query}")
    print("=" * 60)

    full_response = ""
    async for chunk in stream_rag_chat(query):
        print(chunk, end="", flush=True)
        full_response += chunk

    print("\n")
    print("=" * 60)
    print("Verification:")

    if "Page:" in full_response or "page" in full_response.lower():
        print("[PASS] Response contains page number references")
    else:
        print("[FAIL] Response does NOT contain page number references")

    if "Source:" in full_response or "source" in full_response.lower():
        print("[PASS] Response contains source references")
    else:
        print("[FAIL] Response does NOT contain source references")

    if (
        "Q-learning" in full_response
        or "reinforcement learning" in full_response.lower()
    ):
        print("[PASS] Response contains key methodology details")
    else:
        print("[FAIL] Response missing key methodology details")


if __name__ == "__main__":
    asyncio.run(main())
