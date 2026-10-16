"""Orquestrador: liga as etapas online do fluxograma.

tema -> retriever (Chroma) -> prompt -> LLM (+LoRA) -> validação -> resultado
"""
from config import TOP_K
from llm import Gerador
from prompt import montar_mensagens
from retriever import buscar, formatar_fontes
from validate import validar_post


class PipelinePost:
    def __init__(self, usar_lora: bool = True):
        self.gerador = Gerador(usar_lora=usar_lora)

    def gerar(self, tema: str, k: int = TOP_K) -> dict:
        resultados = buscar(tema, k=k)
        trechos = [doc.page_content for doc, _ in resultados]

        mensagens = montar_mensagens(tema, trechos)
        bruto = self.gerador.gerar(mensagens)
        validado = validar_post(bruto)

        return {
            "tema": tema,
            "trechos": trechos,
            "fontes": formatar_fontes(resultados),
            "post": validado.texto,
            "avisos": validado.avisos,
            "ok": validado.ok,
        }
