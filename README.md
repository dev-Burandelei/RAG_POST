# Gerador de posts (RAG + LoRA)

Fluxo: PDFs -> chunks -> embeddings -> Chroma | tema -> busca top-k -> prompt -> LLM (+LoRA) -> validação -> revisão humana

## Módulos

| Arquivo | Etapa do fluxograma |
|---|---|
| `config.py` | parâmetros de todas as etapas |
| `embeddings.py` | modelo de embeddings (igual na indexação e na consulta) |
| `index.py` | Dados -> Chunking -> Embeddings -> Chroma (offline) |
| `retriever.py` | Input -> Retriever top-k |
| `prompt.py` | Prompt (contexto + tom) |
| `llm.py` | LLM base + adaptador LoRA |
| `validate.py` | Validação e formatação |
| `pipeline.py` | orquestrador das etapas online |
| `main.py` | interface + revisão humana (grava exemplos) |
| `train_lora.py` | Exemplos -> Fine-tuning LoRA -> Adaptador (offline) |

## Ordem para rodar

1. `pip install -r requirements.txt`
2. Coloque os PDFs em `base/` e rode `python index.py`
3. Teste só a recuperação: `python retriever.py "tema do post"`
4. Gere posts: `python main.py --sem-lora`
5. Aprove ou edite os bons: eles vão para `data/exemplos.jsonl`
6. Com algumas dezenas de exemplos: `pip install -r requirements-treino.txt` e `python train_lora.py`
7. `python main.py` passa a usar o adaptador (`adapters/instagram/`)

Regras do jogo:
- Trocou o modelo de embeddings ou o chunking: apague `db/` e rode `index.py`.
- Mudou o `SYSTEM_PROMPT` em `prompt.py`: retreine o LoRA.
