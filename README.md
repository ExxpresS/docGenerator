# Workflow Manager

Application web pour capturer, documenter et interroger des workflows métier via RAG/LLM.

## 🚀 Démarrage Rapide

### Développement Local

```bash
# 1. Copier configuration
cp .env.example .env

# 2. Lancer tout
docker-compose up -d

# 3. Accéder
# Frontend: http://localhost:3001
# API Docs: http://localhost:8001/docs
```

### Extension Browser

Pour capturer des workflows directement depuis votre navigateur :

1. Ouvrir Chrome et aller à `chrome://extensions/`
2. Activer "Mode développeur"
3. Cliquer "Charger l'extension non empaquetée"
4. Sélectionner le dossier `extension/`

Voir [extension/README.md](extension/README.md) pour plus de détails.

### Installation Serveur

Voir [docs/INSTALL.md](docs/INSTALL.md)

```bash
./scripts/install.sh
```

## 📚 Documentation

- [Guide Installation](docs/INSTALL.md)
- [Extension Browser](extension/README.md)
- [API Documentation](http://localhost:8001/docs)

## 🏗️ Architecture

```
Extension Browser → Backend (FastAPI) → PostgreSQL + pgvector
                         ↓
                    Frontend (Vue 3)
                         ↓
                    LLM (Ollama/OpenAI/Claude)
```

## 🔧 Configuration

Tout se configure via `.env` :

```env
# LLM Provider
DEFAULT_LLM_PROVIDER=ollama  # ou openai/anthropic

# Si Ollama (local, gratuit)
OLLAMA_MODEL=llama3.2:3b

# Si OpenAI
OPENAI_API_KEY=sk-...

# Si Anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

## 📦 Stack Technique

- **Backend** : FastAPI, psycopg2, Haystack
- **Frontend** : Vue 3, Vite
- **Database** : PostgreSQL 15 + pgvector
- **LLM** : Ollama (local) ou OpenAI/Anthropic (API)
- **Déploiement** : Docker Compose

## 🎯 Phase de Développement

### Phase 1 : Infrastructure Backend ✅

- [x] API REST FastAPI
- [x] Docker Compose setup
- [x] PostgreSQL + pgvector
- [x] Endpoints CRUD projects
- [x] Endpoints CRUD workflows
- [x] Frontend de base

### Phase 2 : Documents & Versioning ✅

- [x] Tables documents + versions
- [x] CRUD documents complet
- [x] Génération automatique (Workflow JSON → Markdown)
- [x] Versioning automatique
- [x] Workflow de statut (draft → validated → published)
- [x] Interface frontend pour documents

### Phase 3 : Extension Browser ✅

- [x] Extension Chrome/Firefox
- [x] Capture d'événements (clicks, inputs, navigation)
- [x] Sync automatique vers backend
- [x] Détection de doublons par hash
- [x] Interface popup de contrôle

### Phase 4-7 : À venir

- [ ] RAG Implementation (chunks + embeddings)
- [ ] LLM Integration (multi-provider)
- [ ] Chat Interface (WebSocket)
- [ ] Production hardening

## 📄 License

MIT
