"""Interface de linha de comando com revisão humana.

    python main.py              # com adaptador LoRA (se existir)
    python main.py --sem-lora   # só o modelo base (para comparar)

Posts aprovados ou editados são salvos em data/exemplos.jsonl: viram
exemplos para o próximo treino do LoRA.
"""
import json
import sys

from config import ARQUIVO_EXEMPLOS
from pipeline import PipelinePost


def salvar_exemplo(tema: str, trechos: list[str], post: str) -> None:
    ARQUIVO_EXEMPLOS.parent.mkdir(parents=True, exist_ok=True)
    registro = {"tema": tema, "contexto": trechos, "post": post}
    with open(ARQUIVO_EXEMPLOS, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")
    print(f"Salvo em {ARQUIVO_EXEMPLOS.name}.")


def ler_multilinha() -> str:
    print("Cole o texto final e termine com uma linha contendo apenas FIM:")
    linhas = []
    while True:
        linha = input()
        if linha.strip() == "FIM":
            break
        linhas.append(linha)
    return "\n".join(linhas).strip()


def mostrar(resultado: dict) -> None:
    print("\n" + "=" * 60)
    print(resultado["post"] or "(vazio)")
    print("=" * 60)
    print("Fontes:", "; ".join(resultado["fontes"]) or "nenhuma")
    for aviso in resultado["avisos"]:
        print("Aviso:", aviso)


def main() -> None:
    pipeline = PipelinePost(usar_lora="--sem-lora" not in sys.argv)

    while True:
        tema = input("\nTema do post (ENTER para sair): ").strip()
        if not tema:
            break

        resultado = pipeline.gerar(tema)
        while True:
            mostrar(resultado)
            opcao = input("[a]provar  [e]ditar  [r]egerar  [d]escartar: ").strip().lower()

            if opcao == "a" and resultado["ok"]:
                salvar_exemplo(tema, resultado["trechos"], resultado["post"])
                break
            if opcao == "e":
                editado = ler_multilinha()
                if editado:
                    salvar_exemplo(tema, resultado["trechos"], editado)
                break
            if opcao == "r":
                resultado = pipeline.gerar(tema)
            elif opcao == "d":
                break


if __name__ == "__main__":
    main()
