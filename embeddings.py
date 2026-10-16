"""Modelo de embeddings compartilhado.

Indexação e consulta PRECISAM usar exatamente o mesmo modelo, por isso ele
vive num módulo só.

Os modelos E5 foram treinados com prefixos: "passage: " nos textos indexados
e "query: " nas perguntas. Sem eles a qualidade da busca cai.
"""
from langchain_huggingface import HuggingFaceEmbeddings

from config import MODELO_EMBEDDINGS


class E5Embeddings(HuggingFaceEmbeddings):
    def embed_documents(self, texts):
        return super().embed_documents([f"passage: {t}" for t in texts])

    def embed_query(self, text):
        return super().embed_query(f"query: {text}")


def get_embeddings():
    return E5Embeddings(
        model_name=MODELO_EMBEDDINGS,
        encode_kwargs={"normalize_embeddings": True},
    )
