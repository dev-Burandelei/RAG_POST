
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "base"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {
    ".pdf", ".txt", ".md", ".docx", ".csv"
}

MAX_FILE_SIZE = 50 * 1024 * 1024


@router.get("/api/arquivos")
def listar_arquivos():
    arquivos = []

    for path in sorted(UPLOAD_DIR.iterdir()):
        if path.is_file() and not path.is_symlink():
            arquivos.append({
                "nome": path.name,
                "tamanho": path.stat().st_size,
            })

    return {"arquivos": arquivos}


@router.post("/api/upload")
async def upload_arquivos(
    files: list[UploadFile] = File(...)
):
    resultados = []

    for file in files:
        original = Path(file.filename or "").name
        extensao = Path(original).suffix.lower()

        if not original or extensao not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Arquivo não permitido: {original}",
            )

        nome = f"{uuid4().hex}_{original}"
        destino = UPLOAD_DIR / nome
        tamanho = 0

        try:
            with destino.open("wb") as output:
                while True:
                    chunk = await file.read(1024 * 1024)

                    if not chunk:
                        break

                    tamanho += len(chunk)

                    if tamanho > MAX_FILE_SIZE:
                        raise HTTPException(
                            status_code=413,
                            detail=f"{original} excede o limite de 50 MB.",
                        )

                    output.write(chunk)

            resultados.append({
                "nome": nome,
                "tamanho": tamanho,
            })

        except Exception:
            destino.unlink(missing_ok=True)
            raise
        finally:
            await file.close()

    return {
        "message": "Upload concluído.",
        "arquivos": resultados,
    }


@router.delete("/api/arquivos/{nome}")
def excluir_arquivo(nome: str):
    # Só permite excluir arquivos diretamente dentro de base/.
    if not nome or Path(nome).name != nome:
        raise HTTPException(400, "Nome de arquivo inválido.")

    destino = UPLOAD_DIR / nome

    if destino.is_symlink() or not destino.is_file():
        raise HTTPException(404, "Arquivo não encontrado.")

    destino.unlink()

    return {"message": f"Arquivo {nome} excluído."}
