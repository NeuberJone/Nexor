#!/bin/bash

# Nexor — Script de Inicialização

echo "🚀 Nexor — Sistema de Gerenciamento de Produção Têxtil"
echo "=================================================="
echo ""

# Ativar ambiente virtual
if [ ! -d "venv" ]; then
  echo "📦 Criando ambiente virtual..."
  python3 -m venv venv
fi

echo "✅ Ativando ambiente virtual..."
source venv/bin/activate

# Instalar dependências
echo "📚 Instalando dependências..."
pip install -q -r requirements.txt

# Executar servidor
echo ""
echo "🌐 Iniciando servidor Flask..."
echo "   URL: http://localhost:5001"
echo "   Backend: http://localhost:5000/api"
echo ""
echo "Pressione CTRL+C para parar"
echo ""

PORT=5001 python main.py
