
import json
from functools import lru_cache

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from config import ARQUIVO_EXEMPLOS
from upload import router as upload_router

app = FastAPI(title="RAG Post Studio")
app.include_router(upload_router)


@lru_cache(maxsize=2)
def obter_pipeline(usar_lora: bool):
    # Importação tardia: evita carregar Transformers
    # ao iniciar o servidor ou abrir a interface.
    from pipeline import PipelinePost

    return PipelinePost(usar_lora=usar_lora)


class GeracaoRequest(BaseModel):
    tema: str = Field(min_length=1, max_length=1000)
    usar_lora: bool = True


class RevisaoRequest(BaseModel):
    tema: str
    trechos: list[str] = []
    post: str = ""
    acao: str


def salvar_exemplo(tema, trechos, post):
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
        resultado = obter_pipeline(request.usar_lora).gerar(tema)

        return {
            "tema": tema,
            "post": resultado.get("post", ""),
            "trechos": resultado.get("trechos", []),
            "fontes": resultado.get("fontes", []),
            "avisos": resultado.get("avisos", []),
            "ok": resultado.get("ok", False),
        }
    except Exception as erro:
        raise HTTPException(
            status_code=500,
            detail=f"Falha na geração: {erro}",
        ) from erro


@app.post("/api/revisar")
def revisar(request: RevisaoRequest):
    if request.acao not in {"aprovar", "editar"}:
        raise HTTPException(400, "Ação inválida.")

    if not request.tema.strip() or not request.post.strip():
        raise HTTPException(400, "Tema e post são obrigatórios.")

    if len(request.post) > 100_000:
        raise HTTPException(400, "O texto é muito grande.")

    salvar_exemplo(
        request.tema.strip(),
        request.trechos,
        request.post.strip(),
    )

    return {"message": "Exemplo salvo em exemplos.jsonl."}


HTML = r"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RAG Post Studio</title>
<style>
*{box-sizing:border-box}
body{margin:0;background:#0b1120;color:#e5e7eb;
font:15px 'Segoe UI',Arial,sans-serif}
.layout{display:flex;min-height:100vh}
aside{width:235px;padding:25px 16px;background:#111827;
border-right:1px solid #293548;flex-shrink:0}
.brand{font-size:21px;font-weight:700;padding:8px 10px 28px}
.nav{display:block;width:100%;text-align:left;margin:6px 0;
padding:13px;border:0;border-radius:8px;background:transparent;
color:#cbd5e1;cursor:pointer}
.nav.active,.nav:hover{background:#24334b;color:white}
main{width:100%;max-width:1100px;margin:auto;padding:34px 28px}
header{margin-bottom:25px}
h1{font-size:29px;margin:0 0 8px}
h2{font-size:19px;margin-top:0}
.sub,.muted{color:#94a3b8}
.sub{line-height:1.6}
.panel{background:#111b2e;border:1px solid #29384f;
border-radius:13px;padding:22px;margin-bottom:18px}
label{display:block;margin-bottom:9px;font-weight:600}
textarea,input[type=text],input[type=file]{
width:100%;padding:12px;background:#0b1120;color:#f8fafc;
border:1px solid #37465c;border-radius:8px}
textarea{resize:vertical;line-height:1.6}
button{padding:11px 15px;border:0;border-radius:8px;
font-weight:600;cursor:pointer}
button:disabled{opacity:.5;cursor:wait}
.primary{background:#60a5fa;color:#0b1120}
.secondary{background:#263750;color:#e5e7eb}
.good{background:#34d399;color:#052e25}
.danger{background:#7f1d1d;color:white}
.actions{display:flex;gap:9px;flex-wrap:wrap;margin-top:15px}
.row{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.row label{margin:0}
.view{display:none}.view.active{display:block}
.file{display:flex;align-items:center;justify-content:space-between;
gap:12px;padding:13px 0;border-bottom:1px solid #29384f}
.file:last-child{border-bottom:0}
.filename{overflow-wrap:anywhere}
.small{font-size:12px;color:#94a3b8;margin-top:4px}
ul{padding-left:22px;overflow-wrap:anywhere}
li{margin:8px 0}
.status{white-space:pre-wrap;margin-top:14px;color:#93c5fd}
@media(max-width:700px){
.layout{display:block}aside{width:100%;padding:12px}
.brand{padding:8px}.nav{display:inline-block;width:auto;margin:3px}
main{padding:22px 13px}.panel{padding:16px}
}
</style>
</head>
<body>
<div class="layout">
<aside>
  <div class="brand">✦ RAG Post Studio</div>
  <button class="nav active" data-view="gerador">✍ Gerar posts</button>
  <button class="nav" data-view="documentos">▤ Documentos</button>
  <div class="small" style="padding:18px 10px">
    Geração com RAG · Revisão humana
  </div>
</aside>

<main>
<section id="gerador" class="view active">
<header>
  <h1>Gerador de posts</h1>
  <div class="sub">Crie conteúdo com base nos documentos recuperados
  pelo seu pipeline RAG.</div>
</header>

<div class="panel">
  <label for="tema">Qual é o tema do post?</label>
  <textarea id="tema" rows="3"
    placeholder="Ex.: Benefícios da IA na produtividade"></textarea>
  <div class="row" style="margin-top:15px">
    <input type="checkbox" id="lora" checked>
    <label for="lora">Usar LoRA (se disponível)</label>
  </div>
  <div class="actions">
    <button class="primary" id="btnGerar" onclick="gerar()">✦ Gerar resposta</button>
  </div>
  <div id="statusGeracao" class="status" role="status"></div>
</div>

<div id="resultado" class="panel" hidden>
  <h2>Resposta gerada</h2>
  <textarea id="post" rows="9"></textarea>

  <h3>Fontes</h3><ul id="fontes"></ul>
  <h3>Trechos recuperados</h3><ul id="trechos"></ul>
  <h3>Avisos</h3><ul id="avisos"></ul>

  <div class="actions">
    <button class="good" onclick="revisar('aprovar')">✓ Aprovar</button>
    <button class="secondary" onclick="revisar('editar')">Salvar edição</button>
    <button class="secondary" onclick="gerar()">↻ Regerar</button>
    <button class="danger" onclick="descartar()">Descartar</button>
  </div>
  <div id="statusRevisao" class="status" role="status"></div>
</div>
</section>

<section id="documentos" class="view">
<header>
  <h1>Base de conhecimento</h1>
  <div class="sub">Envie e gerencie os documentos usados pelo projeto.</div>
</header>

<div class="panel">
  <h2>Adicionar documentos</h2>
  <p class="muted">PDF, TXT, Markdown, DOCX e CSV. Até 50 MB por arquivo.</p>
  <input id="files" type="file" multiple
    accept=".pdf,.txt,.md,.docx,.csv">
  <div class="actions">
    <button class="primary" id="btnUpload" onclick="enviar()">Enviar arquivos</button>
    <button class="secondary" onclick="listarArquivos()">Atualizar lista</button>
  </div>
  <div id="statusUpload" class="status" role="status"></div>
</div>

<div class="panel">
  <h2>Arquivos armazenados</h2>
  <div id="listaArquivos" class="muted">Carregando arquivos...</div>
</div>
</section>
</main>
</div>

<script>
let atual = null;

document.querySelectorAll(".nav").forEach(botao => {
  botao.addEventListener("click", () => {
    document.querySelectorAll(".nav").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));
    botao.classList.add("active");
    document.getElementById(botao.dataset.view).classList.add("active");
    if (botao.dataset.view === "documentos") listarArquivos();
  });
});

function lista(id, itens) {
  const el = document.getElementById(id);
  el.replaceChildren();
  if (!itens || !itens.length) {
    const li = document.createElement("li");
    li.textContent = "Nenhum item disponível.";
    el.appendChild(li);
    return;
  }
  for (const item of itens) {
    const li = document.createElement("li");
    li.textContent = String(item);
    el.appendChild(li);
  }
}

async function gerar() {
  const tema = document.getElementById("tema").value.trim();
  const status = document.getElementById("statusGeracao");
  const botao = document.getElementById("btnGerar");

  if (!tema) { status.textContent = "Informe um tema."; return; }

  botao.disabled = true;
  status.textContent = "Gerando resposta... O modelo pode demorar.";
  document.getElementById("resultado").hidden = true;

  try {
    const res = await fetch("/api/gerar", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({
        tema, usar_lora: document.getElementById("lora").checked
      })
    });
    const data = await res.json();
    if (!res.ok) throw Error(data.detail || "Falha na geração.");

    atual = data;
    document.getElementById("post").value = data.post || "";
    lista("fontes", data.fontes);
    lista("trechos", data.trechos);
    lista("avisos", data.avisos);
    document.getElementById("resultado").hidden = false;
    status.textContent = data.ok
      ? "Geração concluída."
      : "Atenção: o pipeline sinalizou ressalvas. Revise antes de aprovar.";
  } catch (e) {
    status.textContent = "Erro: " + e.message;
  } finally {
    botao.disabled = false;
  }
}

async function revisar(acao) {
  if (!atual) return;
  const status = document.getElementById("statusRevisao");

  if (acao === "aprovar" && !atual.ok) {
    status.textContent = "A resposta não passou na validação do pipeline. Use Salvar edição após revisar.";
    return;
  }

  const post = document.getElementById("post").value.trim();
  if (!post) { status.textContent = "O post não pode estar vazio."; return; }

  try {
    const res = await fetch("/api/revisar", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({
        tema: atual.tema, trechos: atual.trechos, post, acao
      })
    });
    const data = await res.json();
    if (!res.ok) throw Error(data.detail || "Falha ao salvar.");
    status.textContent = data.message;
  } catch (e) {
    status.textContent = "Erro: " + e.message;
  }
}

function descartar() {
  atual = null;
  document.getElementById("resultado").hidden = true;
  document.getElementById("statusRevisao").textContent =
    "Resposta descartada sem salvar.";
}

function formatarBytes(n) {
  if (n < 1024) return n + " B";
  if (n < 1024 * 1024) return (n / 1024).toFixed(1) + " KB";
  return (n / (1024 * 1024)).toFixed(1) + " MB";
}

async function listarArquivos() {
  const el = document.getElementById("listaArquivos");
  el.textContent = "Carregando...";
  try {
    const res = await fetch("/api/arquivos");
    const data = await res.json();
    if (!res.ok) throw Error(data.detail || "Falha ao listar.");

    el.replaceChildren();
    if (!data.arquivos.length) {
      el.textContent = "Nenhum documento enviado ainda.";
      return;
    }

    for (const arquivo of data.arquivos) {
      const row = document.createElement("div");
      row.className = "file";

      const info = document.createElement("div");
      const name = document.createElement("div");
      name.className = "filename";
      name.textContent = arquivo.nome;
      const size = document.createElement("div");
      size.className = "small";
      size.textContent = formatarBytes(arquivo.tamanho);
      info.append(name, size);

      const del = document.createElement("button");
      del.className = "danger";
      del.textContent = "Excluir";
      del.onclick = () => excluirArquivo(arquivo.nome);

      row.append(info, del);
      el.appendChild(row);
    }
  } catch (e) {
    el.textContent = "Erro: " + e.message;
  }
}

async function enviar() {
  const input = document.getElementById("files");
  const status = document.getElementById("statusUpload");
  const botao = document.getElementById("btnUpload");
  if (!input.files.length) {
    status.textContent = "Selecione pelo menos um arquivo.";
    return;
  }

  const form = new FormData();
  for (const file of input.files) form.append("files", file);

  botao.disabled = true;
  status.textContent = "Enviando...";
  try {
    const res = await fetch("/api/upload", {method:"POST", body:form});
    const data = await res.json();
    if (!res.ok) throw Error(data.detail || "Falha no upload.");
    status.textContent = data.message + " " +
      data.arquivos.map(f => f.nome).join(", ");
    input.value = "";
    await listarArquivos();
  } catch (e) {
    status.textContent = "Erro: " + e.message;
  } finally {
    botao.disabled = false;
  }
}

async function excluirArquivo(nome) {
  if (!confirm("Deseja excluir " + nome + "?")) return;
  try {
    const res = await fetch("/api/arquivos/" + encodeURIComponent(nome), {
      method: "DELETE"
    });
    const data = await res.json();
    if (!res.ok) throw Error(data.detail || "Falha ao excluir.");
    await listarArquivos();
  } catch (e) {
    document.getElementById("listaArquivos").textContent =
      "Erro: " + e.message;
  }
}
</script>
</body>
</html>
"""
