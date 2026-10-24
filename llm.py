import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from config import ADAPTADOR_LORA, MAX_NOVOS_TOKENS, MODELO_LLM, TEMPERATURA


class Gerador:
    def __init__(self, usar_lora: bool = True):
        tem_gpu = torch.cuda.is_available()

        if not tem_gpu:
            num_threads = int(os.getenv("TORCH_NUM_THREADS", "4"))
            torch.set_num_threads(num_threads)

        self.tokenizer = AutoTokenizer.from_pretrained(MODELO_LLM)
        self.modelo = AutoModelForCausalLM.from_pretrained(
            MODELO_LLM,
            torch_dtype=torch.bfloat16 if tem_gpu else torch.float32,
            device_map="auto" if tem_gpu else None,
        )

        self.com_lora = False
        if usar_lora and ADAPTADOR_LORA.exists():
            from peft import PeftModel

            self.modelo = PeftModel.from_pretrained(self.modelo, str(ADAPTADOR_LORA))
            # incorpora os pesos do LoRA no modelo: inferência mais rápida
            self.modelo = self.modelo.merge_and_unload()
            self.com_lora = True
        elif usar_lora:
            print("Aviso: adaptador LoRA não encontrado; usando só o modelo base.")

        self.modelo.eval()

    @torch.inference_mode()
    def gerar(
        self,
        mensagens: list[dict],
        max_novos_tokens: int = MAX_NOVOS_TOKENS,
        temperatura: float = TEMPERATURA,
    ) -> str:
        entradas = self.tokenizer.apply_chat_template(
            mensagens,
            add_generation_prompt=True,
            return_tensors="pt",
            return_dict=True,
        ).to(self.modelo.device)

        if temperatura > 0:
            amostragem = dict(do_sample=True, temperature=temperatura, top_p=0.9)
        else:
            amostragem = dict(do_sample=False)

        saida = self.modelo.generate(
            **entradas,
            max_new_tokens=max_novos_tokens,
            pad_token_id=self.tokenizer.eos_token_id,
            **amostragem,
        )

        # decodifica só o que foi gerado (sem repetir o prompt)
        novos = saida[0][entradas["input_ids"].shape[1]:]
        return self.tokenizer.decode(novos, skip_special_tokens=True).strip()
