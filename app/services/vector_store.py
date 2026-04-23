import os
import torch
from transformers import AutoTokenizer, AutoModel
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings

from app.core.config import settings


class LocalEmbeddings(Embeddings):
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.model.eval()

    def _mean_pooling(self, model_output, attention_mask):
        token_embeddings = model_output[0]
        input_mask_expanded = (
            attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        )
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(
            input_mask_expanded.sum(1), min=1e-9
        )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        inputs = self.tokenizer(
            texts, padding=True, truncation=True, max_length=512, return_tensors="pt"
        )
        with torch.no_grad():
            outputs = self.model(**inputs)
        embeddings = self._mean_pooling(outputs, inputs["attention_mask"])
        return embeddings.numpy().tolist()

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


def get_embeddings():
    return LocalEmbeddings()


def get_vector_db():
    os.makedirs(settings.VECTOR_DB_PATH, exist_ok=True)
    return Chroma(
        embedding_function=get_embeddings(),
        persist_directory=settings.VECTOR_DB_PATH,
    )


def add_documents_to_db(documents):
    vector_db = get_vector_db()
    vector_db.add_documents(documents)
    return len(documents)
