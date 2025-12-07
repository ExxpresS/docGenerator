#!/bin/bash

set -e

echo "🚀 Installation Workflow Manager"
echo "================================"

# Vérifier Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker non installé. Installer Docker d'abord."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose non installé."
    exit 1
fi

# Config
if [ ! -f .env ]; then
    echo "📝 Création configuration..."
    cp .env.example .env

    # Générer secrets
    DB_PASS=$(openssl rand -base64 32)
    SECRET=$(openssl rand -hex 32)

    sed -i.bak "s/CHANGE_ME_STRONG_PASSWORD/$DB_PASS/" .env
    sed -i.bak "s/CHANGE_ME_GENERATE_RANDOM_KEY/$SECRET/" .env
    rm .env.bak

    echo "✅ Configuration créée (.env)"
    echo "⚠️  Éditer .env pour configurer le LLM (OpenAI/Anthropic keys si nécessaire)"

    read -p "Éditer maintenant? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ${EDITOR:-nano} .env
    fi
fi

# Build & Start
echo "🔨 Build des images..."
docker-compose build

echo "🚀 Démarrage des services..."
docker-compose up -d

# Attendre que services démarrent
echo "⏳ Attente démarrage services..."
sleep 15

# Init Ollama
if grep -q "DEFAULT_LLM_PROVIDER=ollama" .env; then
    echo "📥 Téléchargement modèle Ollama..."
    OLLAMA_MODEL=$(grep OLLAMA_MODEL .env | cut -d'=' -f2)
    docker exec workflow-ollama ollama pull ${OLLAMA_MODEL:-llama3.2:3b}
fi

# Vérifications
echo "🔍 Vérification des services..."

if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend opérationnel"
else
    echo "❌ Backend KO - Vérifier les logs: docker-compose logs backend"
fi

if curl -f http://localhost:3000/health > /dev/null 2>&1; then
    echo "✅ Frontend opérationnel"
else
    echo "❌ Frontend KO - Vérifier les logs: docker-compose logs frontend"
fi

echo ""
echo "✅ Installation terminée!"
echo ""
echo "📍 Accès:"
echo "   Frontend: http://localhost:3000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "📖 Documentation: docs/INSTALL.md"
echo "🔧 Logs: docker-compose logs -f"
