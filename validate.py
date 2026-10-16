"""Etapa online 4: validação e formatação do texto gerado (regras determinísticas)."""
import re
from dataclasses import dataclass, field

from config import LIMITE_LEGENDA, MAX_HASHTAGS

RE_HASHTAG = re.compile(r"#\w+", re.UNICODE)


@dataclass
class Resultado:
    texto: str
    avisos: list[str] = field(default_factory=list)
    ok: bool = True


def limpar(texto: str) -> str:
    """Remove resíduos comuns de LLM: cercas de código, 'Legenda:' no início etc."""
    texto = texto.strip()
    texto = re.sub(r"^```\w*\n?|\n?```$", "", texto).strip()
    texto = re.sub(r"^(post|legenda)\s*:\s*", "", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def limitar_hashtags(texto: str, maximo: int) -> tuple[str, int]:
    """Mantém as primeiras `maximo` hashtags. Devolve (texto, total_original)."""
    contador = 0

    def trocar(m):
        nonlocal contador
        contador += 1
        return m.group(0) if contador <= maximo else ""

    novo = RE_HASHTAG.sub(trocar, texto)
    novo = re.sub(r"[ \t]{2,}", " ", novo)
    novo = re.sub(r"[ \t]+\n", "\n", novo)
    return novo.strip(), contador


def validar_post(bruto: str) -> Resultado:
    texto = limpar(bruto)
    avisos: list[str] = []

    if not texto:
        return Resultado("", ["O modelo devolveu texto vazio."], ok=False)

    texto, total = limitar_hashtags(texto, MAX_HASHTAGS)
    if total > MAX_HASHTAGS:
        avisos.append(f"Hashtags cortadas: {total} -> {MAX_HASHTAGS}.")
    elif total == 0:
        avisos.append("O post não tem hashtags.")

    if len(texto) > LIMITE_LEGENDA:
        # corta na última palavra inteira que cabe
        texto = texto[:LIMITE_LEGENDA].rsplit(None, 1)[0]
        avisos.append(f"Texto cortado em {LIMITE_LEGENDA} caracteres.")

    return Resultado(texto, avisos, ok=True)
