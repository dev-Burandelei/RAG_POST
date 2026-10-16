"""Etapa offline: PDFs -> chunks -> embeddings -> ChromaDB.

Rode sempre que os PDFs da pasta base/ mudarem:  python index.py
"""
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import CHUNK_OVERLAP, CHUNK_SIZE, PASTA_BASE, PASTA_DB
from embeddings import get_embeddings


def criar_db():

    # Carregar documentos
    documentos = carregar_documentos()

    print(f"Documentos carregados: {len(documentos)}")

    if not documentos:
        print(f"Nenhum PDF com texto encontrado em '{PASTA_BASE}'.")
        return

    # Dividir os documentos em pedaços de texto (chunks)
    chunks = dividir_chunks(documentos)

    print(f"Chunks criados: {len(chunks)}")

    # Vetorizar os chunks e criar o banco vetorial
    vetorizar_chunks(chunks)


def carregar_documentos():

    carregador = PyPDFDirectoryLoader(
        str(PASTA_BASE),
        glob="*.pdf"
    )

    documentos = carregador.load()

    return documentos


def dividir_chunks(documentos):

    separador_documentos = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        add_start_index=True
    )

    chunks = separador_documentos.split_documents(documentos)

    return chunks


def vetorizar_chunks(chunks):

    # Modelo de embeddings local
    embeddings = get_embeddings()

    # Recria o banco do zero: se rodar de novo sem limpar, o Chroma
    # ADICIONA os chunks e a busca passa a devolver trechos duplicados.
    if PASTA_DB.exists():
        Chroma(
            persist_directory=str(PASTA_DB),
            embedding_function=embeddings
        ).delete_collection()

    # Criação do banco vetorial ChromaDB
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(PASTA_DB)
    )

    print("Banco vetorial criado com sucesso!")


if __name__ == "__main__":
    criar_db()
