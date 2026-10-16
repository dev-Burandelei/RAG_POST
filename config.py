"""Configuração central. Tudo que você vai querer ajustar fica aqui."""
from pathlib import Path

from dotenv import load_dotenv

# Carrega variáveis do .env (ex.: HF_TOKEN, se algum modelo exigir login)
load_dotenv()

RAIZ = Path(__file__).parent

# --- Pastas e arquivos -------------------------------------------------------
PASTA_BASE = RAIZ / "base"                      # PDFs de origem
PASTA_DB = RAIZ / "db"                          # ChromaDB persistido
PASTA_ADAPTADORES = RAIZ / "adapters"
ADAPTADOR_LORA = PASTA_ADAPTADORES / "instagram"
ARQUIVO_EXEMPLOS = RAIZ / "data" / "exemplos.jsonl"   # posts bons (treino LoRA)

# --- Indexação e recuperação (RAG) ------------------------------------------
# Multilíngue (funciona bem com português) e aceita até 512 tokens por chunk.
# Se trocar o modelo, apague a pasta db/ e rode o index.py de novo.
MODELO_EMBEDDINGS = "intfloat/multilingual-e5-small"
CHUNK_SIZE = 1000        # em caracteres (~250 tokens em português)
CHUNK_OVERLAP = 150
TOP_K = 4                # quantos trechos entram no prompt

# --- Geração -----------------------------------------------------------------
# Precisa ser um modelo aberto (Hugging Face) para o LoRA poder ser aplicado.
MODELO_LLM = "Qwen/Qwen2.5-1.5B-Instruct"
MAX_NOVOS_TOKENS = 400
TEMPERATURA = 0.7

# --- Regras do post (usadas no prompt e na validação) -------------------------
TOM_DE_VOZ = "claro, próximo e direto, sem formalidades"   # ajuste ao seu perfil
LIMITE_LEGENDA = 2200    # caracteres
MAX_HASHTAGS = 5         # confira a regra atual do Instagram e ajuste

# --- Treino LoRA -------------------------------------------------------------
LORA_R = 8
LORA_ALPHA = 16
LORA_DROPOUT = 0.05
EPOCAS = 3
TAXA_APRENDIZADO = 2e-4
