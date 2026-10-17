
import json
from functools import lru_cache

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from config import ARQUIVO_EXEMPLOS
from pipeline import PipelinePost

app = FastAPI(title="RAG Post Studio")


@lru_cache(maxsize=2)
def obter_pipeline(usar_lora: bool) -> PipelinePost:
    # Carrega cada versão do pipeline apenas quando necessário.
    return PipelinePost(usar_lora=usar_lora)


class GeracaoRequest(BaseModel):
    tema: str = Field(min_length=1, max_length=1000)
    usar_lora: bool = True


class RevisaoRequest(BaseModel):
    tema: str
    trechos: list[str] = []
    post: str = ""
    acao: str


def salvar_exemplo(tema: str, trechos: list[str], post: str):
    ARQUIVO_EXEMPLOS.parent.mkdir(parents=True, exist_ok=True)

    registro = {
        "tema": tema,
        "contexto": trechos,
        "post": post,
    }

    with open(ARQUIVO_EXEMPLOS, "a", encoding="utf-8") as arquivo:
        arquivo.write(json.dumps(registro, ensure_ascii=False) + "\n")


@app.get("/", response_class=HTMLResponse)
def home():
    return HTML


@app.post("/api/gerar")
def gerar(request: GeracaoRequest):
    tema = request.tema.strip()

    if not tema:
        raise HTTPException(400, "Informe um tema.")

    try:
        pipeline = obter_pipeline(request.usar_lora)
        resultado = pipeline.gerar(tema)

        return {
            "tema": tema,
            "post": resultado.get("post", ""),
            "trechos": resultado.get("trechos", []),
            "fontes": resultado.get("fontes", []),
            "avisos": resultado.get("avisos", []),
            "ok": resultado.get("ok", False),
            "usar_lora": request.usar_lora,
        }
    except Exception as erro:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar o post: {erro}",
        ) from erro


@app.post("/api/revisar")
def revisar(request: RevisaoRequest):
    if request.acao not in {"aprovar", "editar"}:
        raise HTTPException(400, "Ação inválida.")

    if not request.tema.strip() or not request.post.strip():
        raise HTTPException(400, "Tema e post são obrigatórios.")

    if len(request.post) > 100_000:
        raise HTTPException(400, "O post excede o tamanho permitido.")

    salvar_exemplo(
        request.tema.strip(),
        request.trechos,
        request.post.strip(),
    )

    return {"message": "Exemplo salvo com sucesso."}


HTML = r"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RAG Post Studio</title>
<style>
* { box-sizing: border-box; }
body {
    margin: 0;
    font-family: Inter, Segoe UI, Arial, sans-serif;
    background: #0b1120;
    color: #e5e7eb;
}
main { max-width: 1000px; margin: auto; padding: 36px 20px; }
header { margin-bottom: 30px; }
h1 { margin-bottom: 8px; font-size: 30px; }
.subtitle { color: #94a3b8; }
.panel {
    background: #111b2e;
    border: 1px solid #26344c;
    border-radius: 14px;
    padding: 22px;
    margin-bottom: 20px;
}
label { display: block; margin-bottom: 10px; font-weight: 600; }
textarea, input, select {
    width: 100%;
    background: #0b1120;
    border: 1px solid #334155;
    color: #f8fafc;
    border-radius: 8px;
    padding: 12px;
    font: inherit;
}
textarea { resize: vertical; line-height: 1.6; }
button {
    border: 0;
    border-radius: 8px;
    padding: 11px 16px;
    cursor: pointer;
    font-weight: 600;
}
button:disabled { opacity: .5; cursor: wait; }
.primary { background: #60a5fa; color: #0b1120; }
.secondary { background: #26344c; color: #e5e7eb; }
.success { background: #34d399; color: #052e25; }
.danger { background: #7f1d1d; color: #fee2e2; }
.actions { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 16px; }
.row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.row input { width: auto; }
.muted { color: #94a3b8; font-size: 13px; }
#status { white-space: pre-wrap; margin-top: 14px; }
#result { display: none; }
h2 { font-size: 19px; }
h3 { font-size: 15px; color: #93c5fd; }
ul { padding-left: 22px; }
li { margin-bottom: 8px; overflow-wrap: anywhere; }
@media(max-width: 600px) {
    main { padding: 22px 12px; }
    .panel { padding: 16px; }
    h1 { font-size: 25px; }
}
</style>
</head>
<body>
<main>
<header>
    <h1>RAG Post Studio</h1>
    <div class="subtitle">
        Gere, consulte as fontes e revise posts produzidos pelo seu RAG.
    </div>
</header>

<section class="panel">
    <label for="tema">Tema do post</label>
    <textarea id="tema" rows="3"
        placeholder="Ex.: Como a IA está transformando o trabalho"></textarea>

    <div class="row" style="margin-top:16px">
        <input type="checkbox" id="lora" checked>
        <label for="lora" style="margin:0">Usar adaptador LoRA (se disponível)</label>
    </div>

    <div class="actions">
        <button class="primary" id="generate" onclick="gerar()">
            Gerar post
        </button>
    </div>
    <div id="status" class="muted" role="status"></div>
</section>

<section class="panel" id="result">
    <h2>Resposta gerada</h2>
    <textarea id="post" rows="10"
        aria-label="Texto do post, editável"></textarea>

    <h3>Fontes recuperadas</h3>
    <ul id="fontes"></ul>

    <h3>Trechos de contexto</h3>
    <ul id="trechos"></ul>

    <h3>Avisos do pipeline</h3>
    <ul id="avisos"></ul>

    <div class="actions">
        <button class="success" onclick="revisar('aprovar')">
            Aprovar e salvar
        </button>
        <button class="secondary" onclick="revisar('editar')">
            Salvar versão editada
        </button>
        <button class="secondary" onclick="gerar()">
            Gerar novamente
        </button>
        <button class="danger" onclick="descartar()">
            Descartar
        </button>
    </div>
    <div id="reviewStatus" class="muted" role="status"></div>
</section>
</main>

<script>
let atual = null;

function preencherLista(id, itens) {
    const lista = document.getElementById(id);
    lista.replaceChildren();

    if (!itens || itens.length === 0) {
        const li = document.createElement("li");
        li.textContent = "Nenhum item disponível.";
        lista.appendChild(li);
        return;
    }

    for (const item of itens) {
        const li = document.createElement("li");
        li.textContent = String(item);
        lista.appendChild(li);
    }
}

async function gerar() {
    const tema = document.getElementById("tema").value.trim();
    const status = document.getElementById("status");
    const botao = document.getElementById("generate");

    if (!tema) {
        status.textContent = "Digite um tema antes de gerar.";
        return;
    }

    botao.disabled = true;
    status.textContent = "Gerando resposta. O modelo pode levar algum tempo...";
    document.getElementById("reviewStatus").textContent = "";
    document.getElementById("result").style.display = "none";

    try {
        const response = await fetch("/api/gerar", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                tema,
                usar_lora: document.getElementById("lora").checked
            })
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Falha na geração.");

        atual = data;
        document.getElementById("post").value = data.post || "";
        preencherLista("fontes", data.fontes);
        preencherLista("trechos", data.trechos);
        preencherLista("avisos", data.avisos);

        document.getElementById("result").style.display = "block";
        status.textContent = data.ok
            ? "Geração concluída."
            : "Resposta gerada com ressalvas. Confira os avisos antes de aprovar.";
    } catch (error) {
        status.textContent = "Erro: " + error.message;
    } finally {
        botao.disabled = false;
    }
}

async function revisar(acao) {
    if (!atual) return;

    if (acao === "aprovar" && !atual.ok) {
        document.getElementById("reviewStatus").textContent =
            "O pipeline sinalizou que a resposta não está OK. Revise-a e salve como versão editada se desejar.";
        return;
    }

    const post = document.getElementById("post").value.trim();
    const status = document.getElementById("reviewStatus");
    if (!post) {
        status.textContent = "O texto não pode estar vazio.";
        return;
    }

    try {
        const response = await fetch("/api/revisar", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                tema: atual.tema,
                trechos: atual.trechos,
                post,
                acao
            })
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Falha ao salvar.");

        status.textContent = data.message;
    } catch (error) {
        status.textContent = "Erro: " + error.message;
    }
}

function descartar() {
    atual = null;
    document.getElementById("result").style.display = "none";
    document.getElementById("reviewStatus").textContent = "";
    document.getElementById("status").textContent =
        "Resposta descartada. Nenhum exemplo foi salvo.";
}
</script>
</body>
</html>
"""
