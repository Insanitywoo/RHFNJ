from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma

from app.services.vector_store import LocalEmbeddings
from app.core.config import settings


def load_pdf(file_path: str):
    loader = PyMuPDFLoader(file_path)
    return loader.load()


def get_parent_splitter():
    return RecursiveCharacterTextSplitter(
        chunk_size=5000,
        chunk_overlap=500,
        add_start_index=True,
    )


def process_pdf(file_path: str):
    docs = load_pdf(file_path)
    for doc in docs:
        doc.metadata = {
            "source": file_path,
            "page": doc.metadata.get("page", 0),
        }
    splitter = get_parent_splitter()
    return splitter.split_documents(docs)


def get_vector_db(path: str = None):
    if path is None:
        path = settings.VECTOR_DB_PATH
    embeddings = LocalEmbeddings()
    return Chroma(
        embedding_function=embeddings,
        persist_directory=path,
    )


def index_pdf(file_path: str, vector_store_path: str = None):
    if vector_store_path is None:
        vector_store_path = settings.VECTOR_DB_PATH

    docs = load_pdf(file_path)
    for doc in docs:
        doc.metadata = {
            "source": file_path,
            "page": doc.metadata.get("page", 0),
        }

    splitter = get_parent_splitter()
    chunks = splitter.split_documents(docs)

    embeddings = LocalEmbeddings()
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=vector_store_path,
    )

    return len(chunks)
