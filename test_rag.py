import sys
from pathlib import Path

from app.services.pdf_processor import process_pdf
from app.services.vector_store import get_vector_db


def search_similar(query: str, k: int = 3):
    vector_db = get_vector_db()
    results = vector_db.similarity_search(query, k=k)
    return results


def main(pdf_path: str):
    print(f"Processing PDF: {pdf_path}")
    print("-" * 50)

    chunks = process_pdf(pdf_path)
    print(f"Created {len(chunks)} chunks")

    from app.services.vector_store import add_documents_to_db

    add_documents_to_db(chunks)
    print("Indexed to vector database")

    print("\n" + "=" * 50)
    print("Searching: 'What reinforcement learning algorithm is used?'")
    print("=" * 50)

    results = search_similar("What reinforcement learning algorithm is used?", k=3)
    for i, doc in enumerate(results, 1):
        print(f"\n[Result {i}]")
        print(f"Source: {doc.metadata.get('source')}")
        print(f"Page: {doc.metadata.get('page')}")
        print(f"Content: {doc.page_content[:200]}...")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_rag.py <pdf_path>")
        sys.exit(1)
    main(sys.argv[1])
