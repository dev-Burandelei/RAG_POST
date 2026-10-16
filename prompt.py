"""Etapa online 2: monta o prompt (sistema + contexto + pedido).

ATENÇÃO: o treino LoRA usa estas mesmas funções. Se mudar o SYSTEM_PROMPT
ou o formato abaixo depois de treinar, retreine o adaptador.
"""
from config import LIMITE_LEGENDA, MAX_HASHTAGS, TOM_DE_VOZ

SYSTEM_PROMPT = f"""Você é redator de posts para Instagram, em português do Brasil.
Tom de voz: {TOM_DE_VOZ}.

Regras:
- Use somente fatos que estejam no CONTEXTO. Se o contexto não trouxer o dado, não invente.
- A primeira linha é um gancho curto que prende a atenção.
- No máximo {LIMITE_LEGENDA} caracteres.
- Feche com uma chamada para ação e no máximo {MAX_HASHTAGS} hashtags.
- Responda apenas com o texto do post, sem explicações."""


def formatar_contexto(trechos: list[str]) -> str:
    if not trechos:
        return "(nenhum contexto encontrado)"
    return "\n\n".join(f"[{i}] {t.strip()}" for i, t in enumerate(trechos, start=1))


def montar_mensagens(tema: str, trechos: list[str]) -> list[dict]:
    """Mensagens no formato de chat (role/content), prontas para o tokenizer."""
    usuario = (
        f"CONTEXTO:\n{formatar_contexto(trechos)}\n\n"
        f"TEMA DO POST: {tema.strip()}"
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": usuario},
    ]
