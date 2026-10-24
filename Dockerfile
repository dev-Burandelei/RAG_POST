FROM python:3.11-slim

# Evita arquivos .pyc e garante logs em tempo real
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    HOST=0.0.0.0 \
    TORCH_NUM_THREADS=4

WORKDIR /app

# Dependências mínimas de compilação para Linux/ARM64
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Cache de dependências do Python
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Cria diretórios persistentes
RUN mkdir -p /app/base /app/db /app/data /app/adapters

# Copia a aplicação
COPY . /app

EXPOSE 8000

CMD ["uvicorn", "webapp:app", "--host", "0.0.0.0", "--port", "8000"]
