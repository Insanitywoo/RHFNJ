from pathlib import Path

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.services.vector_store import get_vector_db


def load_pdf(file_path: Path):
    loader = PyMuPDFLoader(str(file_path))
    return loader.load()


def get_text_splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        add_start_index=True,
    )


def build_chunks(file_path: Path):
    docs = load_pdf(file_path)
    source_name = file_path.name
    for doc in docs:
        page_number = int(doc.metadata.get("page", 0)) + 1
        doc.metadata = {
            "source": str(file_path),
            "source_name": source_name,
            "page": page_number,
        }
    return get_text_splitter().split_documents(docs)


def index_pdf(file_path: Path) -> int:
    chunks = build_chunks(file_path)
    vector_db = get_vector_db()
    vector_db.add_documents(chunks)
    return len(chunks)
