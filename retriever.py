"""Etapa online 1: pergunta -> embedding -> busca top-k no Chroma.

Teste isolado (antes de ligar o LLM):
    python retriever.py "tema do post"
"""
import sys
from functools import lru_cache
from pathlib import Path

from langchain_chroma import Chroma

from config import PASTA_DB, TOP_K
from embeddings import get_embeddings


@lru_cache(maxsize=1)
def carregar_db():
    if not Path(PASTA_DB).exists():
        raise FileNotFoundError(
            f"Banco vetorial não encontrado em '{PASTA_DB}'. Rode `python index.py` primeiro."
        )
    return Chroma(
        persist_directory=str(PASTA_DB),
        embedding_function=get_embeddings(),
    )


def buscar(pergunta: str, k: int = TOP_K, distancia_maxima: float | None = None):
    """Devolve [(Document, distancia)], do mais parecido ao menos parecido.

    Distância MENOR = mais parecido. Use `distancia_maxima` para descartar
    trechos pouco relevantes (olhe as distâncias reais do seu acervo antes
    de escolher um valor).
    """
    resultados = carregar_db().similarity_search_with_score(pergunta, k=k)
    if distancia_maxima is not None:
        resultados = [(doc, d) for doc, d in resultados if d <= distancia_maxima]
    return resultados


def formatar_fontes(resultados) -> list[str]:
    """['arquivo.pdf, p. 3', ...] para mostrar de onde veio cada trecho."""
    fontes = []
    for doc, _ in resultados:
        arquivo = Path(doc.metadata.get("source", "?")).name
        pagina = doc.metadata.get("page")
        fontes.append(f"{arquivo}, p. {pagina + 1}" if isinstance(pagina, int) else arquivo)
    return fontes


if __name__ == "__main__":
    pergunta = " ".join(sys.argv[1:]) or input("Pergunta: ")
    achados = buscar(pergunta)
    for (doc, distancia), fonte in zip(achados, formatar_fontes(achados)):
        print(f"\n--- distância {distancia:.3f} | {fonte}")
        print(doc.page_content[:400])
