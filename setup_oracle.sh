#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "  Configuracao Automatizada na Oracle Cloud (Ampere A1)   "
echo "  Projeto: RAG_POST (Oficina de Agentes de IA)           "
echo "=========================================================="

# 1. Atualizar pacotes do sistema Ubuntu
echo "[1/5] Atualizando pacotes do sistema..."
sudo apt-get update -y
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    git \
    iptables-persistent \
    netfilter-persistent

# 2. Configurar regras de firewall local (iptables) para portas 80, 443 e 8000
echo "[2/5] Liberando portas 80, 443 e 8000 no firewall local..."
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT 2>/dev/null || sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT 2>/dev/null || sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8000 -j ACCEPT 2>/dev/null || sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
sudo netfilter-persistent save

# 3. Instalar Docker oficial se nao estiver instalado
echo "[3/5] Verificando instalacao do Docker..."
if ! command -v docker &> /dev/null; then
    echo "Instalando Docker Engine e Docker Compose Plugin..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker "$USER"
fi

# 4. Garantir pastas persistentes
echo "[4/5] Garantindo diretorios de persistencia..."
mkdir -p base db data adapters

# Cria .env se nao existir
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "Arquivo .env criado a partir de .env.example"
    fi
fi

# 5. Iniciar containers com Docker Compose
echo "[5/5] Construindo imagem Docker e iniciando container..."
if docker compose version &> /dev/null; then
    sudo docker compose up -d --build
else
    sudo docker-compose up -d --build
fi

IP_PUBLICO=$(curl -s -4 ifconfig.me 2>/dev/null || echo "SEU_IP_PUBLICO")

echo ""
echo "=========================================================="
echo "  ✓ Deploy concluido com sucesso!                         "
echo "  Acesse sua aplicacao no navegador:                     "
echo "  --> http://${IP_PUBLICO}:8000                          "
echo "=========================================================="
echo "Lembrete: Permita a porta 8000 nas Ingress Rules da VCN   "
echo "no painel da Oracle Cloud para liberar o acesso externo!  "
echo "=========================================================="
