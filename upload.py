
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "base"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {
    ".pdf", ".txt", ".md", ".docx", ".csv"
}

HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>RAG - Upload de documentos</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 700px;
            margin: 60px auto;
            padding: 20px;
            background: #f4f6f9;
            color: #202938;
        }
        .card {
            background: white;
            padding: 30px;
            border-radius: 14px;
            box-shadow: 0 4px 20px #0001;
        }
        input, button { margin-top: 16px; }
        button {
            display: block;
            padding: 12px 20px;
            background: #2563eb;
            color: white;
            border: 0;
            border-radius: 8px;
            cursor: pointer;
        }
        #status { margin-top: 20px; }
    </style>
</head>
<body>
    <div class="card">
        <h1>Base de conhecimento RAG</h1>
        <p>Selecione documentos para adicionar à pasta base/.</p>

        <form id="uploadForm">
            <input type="file" id="files" name="files"
                   multiple required
                   accept=".pdf,.txt,.md,.docx,.csv">
            <button type="submit">Enviar arquivos</button>
        </form>

        <p id="status"></p>
    </div>

    <script>
        const form = document.getElementById("uploadForm");
        const status = document.getElementById("status");

        form.addEventListener("submit", async (event) => {
            event.preventDefault();

            const files = document.getElementById("files").files;
            if (!files.length) return;

            const data = new FormData();
            for (const file of files) {
                data.append("files", file);
            }

            status.textContent = "Enviando arquivos...";

            try {
                const response = await fetch("/upload", {
                    method: "POST",
                    body: data
                });

                const result = await response.json();

                if (!response.ok) {
                    throw new Error(result.detail || "Falha no envio");
                }

                status.textContent =
                    "Enviados: " + result.files.join(", ");
                form.reset();
            } catch (error) {
                status.textContent = "Erro: " + error.message;
            }
        });
    </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def home():
    return HTML


@app.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    saved_files = []

    for file in files:
        original_name = Path(file.filename or "").name
        extension = Path(original_name).suffix.lower()

        if not original_name or extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de arquivo não permitido: {original_name}"
            )

        # Nome exclusivo para evitar sobrescrever arquivos existentes.
        filename = f"{uuid4().hex}_{original_name}"
        destination = UPLOAD_DIR / filename

        try:
            with destination.open("wb") as output:
                while chunk := await file.read(1024 * 1024):
                    output.write(chunk)

            saved_files.append(filename)
        finally:
            await file.close()

    return {
        "message": "Upload concluído",
        "files": saved_files
    }
