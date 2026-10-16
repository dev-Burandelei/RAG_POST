"""Etapa offline: treina o adaptador LoRA com data/exemplos.jsonl.

Cada linha do arquivo:
    {"tema": "...", "contexto": ["trecho 1", "trecho 2"], "post": "texto ideal"}
("contexto" pode ser [] ou ficar de fora). O main.py já grava nesse formato
quando você aprova ou edita um post.

Rode:  python train_lora.py
Requer: pip install -r requirements-treino.txt  (e, de preferência, uma GPU)
"""
import json

import torch
from datasets import Dataset
from peft import LoraConfig
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import SFTConfig, SFTTrainer

from config import (
    ADAPTADOR_LORA,
    ARQUIVO_EXEMPLOS,
    EPOCAS,
    LORA_ALPHA,
    LORA_DROPOUT,
    LORA_R,
    MODELO_LLM,
    PASTA_ADAPTADORES,
    TAXA_APRENDIZADO,
)
from prompt import montar_mensagens


def carregar_dataset():
    exemplos = []
    with open(ARQUIVO_EXEMPLOS, encoding="utf-8") as f:
        for linha in f:
            if not linha.strip():
                continue
            item = json.loads(linha)
            contexto = item.get("contexto") or []
            if isinstance(contexto, str):
                contexto = [contexto]
            exemplos.append(
                {
                    # mesmo prompt da geração (prompt.py) ...
                    "prompt": montar_mensagens(item["tema"], contexto),
                    # ... e a resposta ideal. O TRL calcula a perda só na resposta.
                    "completion": [{"role": "assistant", "content": item["post"]}],
                }
            )

    print(f"{len(exemplos)} exemplos carregados.")
    if len(exemplos) < 50:
        print("Aviso: poucos exemplos. Com menos de ~50 o ganho sobre o prompt costuma ser pequeno.")

    dataset = Dataset.from_list(exemplos)
    if len(exemplos) >= 10:
        partes = dataset.train_test_split(test_size=0.1, seed=42)
        return partes["train"], partes["test"]
    return dataset, None


def treinar():
    treino, validacao = carregar_dataset()

    tem_gpu = torch.cuda.is_available()
    usa_bf16 = tem_gpu and torch.cuda.is_bf16_supported()

    tokenizer = AutoTokenizer.from_pretrained(MODELO_LLM)
    modelo = AutoModelForCausalLM.from_pretrained(
        MODELO_LLM,
        torch_dtype=torch.bfloat16 if usa_bf16 else torch.float32,
    )

    config_lora = LoraConfig(
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        target_modules=["q_proj", "v_proj"],
        task_type="CAUSAL_LM",
    )

    config_treino = SFTConfig(
        output_dir=str(PASTA_ADAPTADORES / "checkpoints"),
        num_train_epochs=EPOCAS,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        learning_rate=TAXA_APRENDIZADO,
        logging_steps=5,
        eval_strategy="epoch" if validacao is not None else "no",
        save_strategy="no",
        bf16=usa_bf16,
        report_to="none",
    )

    treinador = SFTTrainer(
        model=modelo,
        args=config_treino,
        train_dataset=treino,
        eval_dataset=validacao,
        peft_config=config_lora,
        processing_class=tokenizer,
    )
    treinador.train()

    # salva só os pesos do LoRA (poucos MB)
    treinador.model.save_pretrained(str(ADAPTADOR_LORA))
    tokenizer.save_pretrained(str(ADAPTADOR_LORA))
    print(f"Adaptador salvo em {ADAPTADOR_LORA}")


if __name__ == "__main__":
    treinar()
