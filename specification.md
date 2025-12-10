todo : 
index all -> reindex que les modifiés 
llm ajouter un agent avec connexion à un ollama / lm studio
chat llm connecté aux rag 


Déploiement Clé en Main - De Dev Local → Serveur Production
🎯 Objectif
Setup local dev → Package déployable facilement → Installation simple au travail
Contraintes :

Développement sur ta machine perso
Déploiement sur serveur au travail
Configuration via .env uniquement
Installation "clé en main"


🚀 SOLUTION RECOMMANDÉE : Docker Compose
Pourquoi Docker ?
✅ Portable : Fonctionne partout (ton PC, serveur boulot, cloud)
✅ Reproductible : Même environnement dev et prod
✅ Isolé : Pas de conflit avec autres applis sur le serveur
✅ Simple : Une commande pour tout démarrer
✅ Clé en main : Juste copier les fichiers + docker-compose up
Architecture Docker
workflow-manager/
├── docker-compose.yml          # Orchestration complète
├── .env.example                # Template config
├── .env                        # Config réelle (git-ignored)
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│
├── frontend/
│   ├── Dockerfile
│   └── src/
│
└── docs/
├── INSTALL.md              # Guide installation serveur
└── QUICKSTART.md

📦 DOCKER COMPOSE COMPLET
docker-compose.yml
yamlversion: '3.8'

services:
# PostgreSQL + pgvector
postgres:
image: pgvector/pgvector:pg15
container_name: workflow-db
environment:
POSTGRES_DB: ${DB_NAME:-workflows_db}
POSTGRES_USER: ${DB_USER:-workflow_user}
POSTGRES_PASSWORD: ${DB_PASSWORD}
POSTGRES_HOST_AUTH_METHOD: ${DB_AUTH_METHOD:-scram-sha-256}
ports:
- "${DB_PORT:-5432}:5432"
volumes:
- postgres_data:/var/lib/postgresql/data
- ./backend/app/db/schema.sql:/docker-entrypoint-initdb.d/01-schema.sql
healthcheck:
test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-workflow_user}"]
interval: 10s
timeout: 5s
retries: 5
restart: unless-stopped

# Backend FastAPI
backend:
build:
context: ./backend
dockerfile: Dockerfile
container_name: workflow-backend
environment:
# Database
DATABASE_URL: postgresql://${DB_USER:-workflow_user}:${DB_PASSWORD}@postgres:5432/${DB_NAME:-workflows_db}

      # API Config
      PROJECT_NAME: ${PROJECT_NAME:-Workflow Manager}
      DEBUG: ${DEBUG:-false}
      API_V1_PREFIX: /api/v1
      
      # CORS
      BACKEND_CORS_ORIGINS: ${FRONTEND_URL:-http://localhost:3000}
      
      # LLM Config
      DEFAULT_LLM_PROVIDER: ${DEFAULT_LLM_PROVIDER:-ollama}
      
      # Ollama
      OLLAMA_BASE_URL: ${OLLAMA_BASE_URL:-http://ollama:11434}
      OLLAMA_MODEL: ${OLLAMA_MODEL:-llama3.2:3b}
      
      # OpenAI (optional)
      OPENAI_API_KEY: ${OPENAI_API_KEY:-}
      OPENAI_MODEL: ${OPENAI_MODEL:-gpt-4o-mini}
      
      # Anthropic (optional)
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:-}
      ANTHROPIC_MODEL: ${ANTHROPIC_MODEL:-claude-sonnet-4-20250514}
      
      # RAG Config
      EMBEDDING_MODEL_NAME: ${EMBEDDING_MODEL_NAME:-sentence-transformers/all-MiniLM-L6-v2}
      CHUNK_SIZE: ${CHUNK_SIZE:-1000}
      CHUNK_OVERLAP: ${CHUNK_OVERLAP:-200}
    ports:
      - "${BACKEND_PORT:-8000}:8000"
    volumes:
      - ./backend/app:/app/app  # Dev: hot reload
      - model_cache:/root/.cache  # Cache embeddings models
    depends_on:
      postgres:
        condition: service_healthy
      ollama:
        condition: service_started
    restart: unless-stopped

# Frontend Vue 3
frontend:
build:
context: ./frontend
dockerfile: Dockerfile
args:
VITE_API_BASE_URL: ${BACKEND_URL:-http://localhost:8000}
container_name: workflow-frontend
ports:
- "${FRONTEND_PORT:-3000}:80"
depends_on:
- backend
restart: unless-stopped

# Ollama (LLM local)
ollama:
image: ollama/ollama:latest
container_name: workflow-ollama
ports:
- "${OLLAMA_PORT:-11434}:11434"
volumes:
- ollama_data:/root/.ollama
environment:
- OLLAMA_KEEP_ALIVE=24h
# Décommenter si GPU disponible
# deploy:
#   resources:
#     reservations:
#       devices:
#         - driver: nvidia
#           count: 1
#           capabilities: [gpu]
restart: unless-stopped

# Nginx reverse proxy (optionnel, recommandé pour prod)
nginx:
image: nginx:alpine
container_name: workflow-nginx
ports:
- "${NGINX_PORT:-80}:80"
- "${NGINX_SSL_PORT:-443}:443"
volumes:
- ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
- ./nginx/ssl:/etc/nginx/ssl:ro  # Certificats SSL si nécessaire
depends_on:
- frontend
- backend
restart: unless-stopped
# Décommenter en production
# profiles:
#   - production

volumes:
postgres_data:
ollama_data:
model_cache:

networks:
default:
name: workflow-network

🔧 FICHIERS DOCKER
backend/Dockerfile
dockerfileFROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
build-essential \
curl \
&& rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download embedding model at build time (optionnel)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Copy application
COPY app/ ./app/

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
frontend/Dockerfile
dockerfile# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source
COPY . .

# Build argument for API URL
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# Build for production
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
frontend/nginx.conf
nginxserver {
listen 80;
server_name _;

    root /usr/share/nginx/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Health check
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}

📄 FICHIER .env TEMPLATE
.env.example
env# ==============================================================================
# WORKFLOW MANAGER - CONFIGURATION
# ==============================================================================
# Copier ce fichier vers .env et remplir les valeurs
# NE PAS COMMITER .env dans Git !

# ------------------------------------------------------------------------------
# DATABASE
# ------------------------------------------------------------------------------
DB_NAME=workflows_db
DB_USER=workflow_user
DB_PASSWORD=CHANGE_ME_STRONG_PASSWORD
DB_PORT=5432
DB_AUTH_METHOD=scram-sha-256

# ------------------------------------------------------------------------------
# APPLICATION
# ------------------------------------------------------------------------------
PROJECT_NAME=Workflow Manager
DEBUG=false
BACKEND_PORT=8000
FRONTEND_PORT=3000
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000

# ------------------------------------------------------------------------------
# LLM PROVIDER (ollama | openai | anthropic)
# ------------------------------------------------------------------------------
DEFAULT_LLM_PROVIDER=ollama

# --- Ollama (Local) ---
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_PORT=11434
OLLAMA_MODEL=llama3.2:3b
# Autres modèles: qwen2.5:7b, mistral:7b, llama3.2:7b

# --- OpenAI (Cloud - optionnel) ---
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini

# --- Anthropic Claude (Cloud - optionnel) ---
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-sonnet-4-20250514

# ------------------------------------------------------------------------------
# RAG CONFIGURATION
# ------------------------------------------------------------------------------
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
RAG_TOP_K_DEFAULT=5

# ------------------------------------------------------------------------------
# NGINX (Production)
# ------------------------------------------------------------------------------
NGINX_PORT=80
NGINX_SSL_PORT=443

# ------------------------------------------------------------------------------
# SECURITY (Générer avec: openssl rand -hex 32)
# ------------------------------------------------------------------------------
SECRET_KEY=CHANGE_ME_GENERATE_RANDOM_KEY

📖 GUIDE D'INSTALLATION SERVEUR
docs/INSTALL.md
markdown# Installation Serveur - Workflow Manager

## Prérequis

- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 20GB espace disque

## Installation

### 1. Transférer les fichiers
```bash
# Sur ton PC local
tar -czf workflow-manager.tar.gz workflow-manager/
scp workflow-manager.tar.gz user@serveur:/opt/

# Sur le serveur
cd /opt
tar -xzf workflow-manager.tar.gz
cd workflow-manager
```

### 2. Configuration
```bash
# Copier le template de config
cp .env.example .env

# Éditer la configuration
nano .env
```

**Configuration minimale requise :**
```env
# Mot de passe base de données (OBLIGATOIRE)
DB_PASSWORD=votre_mot_de_passe_fort

# Provider LLM
DEFAULT_LLM_PROVIDER=ollama  # ou openai/anthropic

# Si OpenAI/Anthropic
OPENAI_API_KEY=sk-...  # Si DEFAULT_LLM_PROVIDER=openai
ANTHROPIC_API_KEY=sk-ant-...  # Si DEFAULT_LLM_PROVIDER=anthropic
```

### 3. Démarrage
```bash
# Lancer tous les services
docker-compose up -d

# Vérifier le statut
docker-compose ps

# Voir les logs
docker-compose logs -f
```

### 4. Initialisation Ollama (si LLM local)
```bash
# Télécharger le modèle
docker exec workflow-ollama ollama pull llama3.2:3b

# Vérifier
docker exec workflow-ollama ollama list
```

### 5. Vérification
```bash
# Backend API
curl http://localhost:8000/health
# Réponse: {"status":"ok"}

# Frontend
curl http://localhost:3000/health
# Réponse: healthy

# Ollama
curl http://localhost:11434/api/tags
# Liste des modèles installés
```

### 6. Accès à l'application

- **Frontend** : http://serveur:3000
- **API Docs** : http://serveur:8000/docs
- **Ollama** : http://serveur:11434

## Maintenance

### Mise à jour
```bash
# Sur ton PC, après modifications
git pull  # ou récupérer nouvelles versions
docker-compose build --no-cache

# Sur serveur
docker-compose pull
docker-compose up -d --build
```

### Backup base de données
```bash
# Backup
docker exec workflow-db pg_dump -U workflow_user workflows_db > backup.sql

# Restore
docker exec -i workflow-db psql -U workflow_user workflows_db < backup.sql
```

### Logs
```bash
# Tous les services
docker-compose logs -f

# Service spécifique
docker-compose logs -f backend
docker-compose logs -f postgres
```

### Arrêt/Redémarrage
```bash
# Arrêt
docker-compose down

# Arrêt + suppression volumes (DANGER: perte données)
docker-compose down -v

# Redémarrage
docker-compose restart

# Redémarrage service spécifique
docker-compose restart backend
```

## Dépannage

### Backend ne démarre pas
```bash
# Vérifier les logs
docker-compose logs backend

# Vérifier la connexion DB
docker exec workflow-backend env | grep DATABASE_URL
```

### Ollama lent
```bash
# Vérifier si GPU détecté
docker exec workflow-ollama nvidia-smi  # Si GPU NVIDIA

# Sinon: CPU only (normal d'être plus lent)
```

### Base de données corrompue
```bash
# Restaurer depuis backup
docker-compose down
docker volume rm workflow-manager_postgres_data
docker-compose up -d postgres
# Attendre que postgres démarre
docker exec -i workflow-db psql -U workflow_user workflows_db < backup.sql
docker-compose up -d
```

🔒 SÉCURITÉ PRODUCTION
Script de génération secrets
scripts/generate-secrets.sh
bash#!/bin/bash

echo "# Secrets générés automatiquement" > .env.secrets
echo "DB_PASSWORD=$(openssl rand -base64 32)" >> .env.secrets
echo "SECRET_KEY=$(openssl rand -hex 32)" >> .env.secrets

echo "✅ Secrets générés dans .env.secrets"
echo "⚠️  Copier dans .env et SUPPRIMER .env.secrets"
nginx/nginx.conf (Reverse Proxy Production)
nginx# Limite upload
client_max_body_size 50M;

# Rate limiting
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=general_limit:10m rate=100r/s;

upstream backend {
server backend:8000;
}

upstream frontend {
server frontend:80;
}

server {
listen 80;
server_name workflow.votreentreprise.com;

    # Redirect to HTTPS (optionnel)
    # return 301 https://$host$request_uri;

    # API Backend
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;
        
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # API Docs
    location /docs {
        proxy_pass http://backend;
        proxy_set_header Host $host;
    }

    # Frontend
    location / {
        limit_req zone=general_limit burst=50 nodelay;
        
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Health checks
    location /health {
        access_log off;
        return 200 "healthy\n";
    }
}

🚀 WORKFLOW COMPLET : Dev → Prod
1. Développement Local (Ta Machine)
   bash# Clone/setup initial
   git clone ton-repo workflow-manager
   cd workflow-manager

# Config locale
cp .env.example .env
nano .env  # Ajuster pour dev local

# Lancer en dev
docker-compose up -d

# Dev avec hot reload
docker-compose -f docker-compose.dev.yml up
2. Préparation Package
   bash# Tester en mode production localement
   docker-compose down
   docker-compose up --build -d

# Vérifier que tout fonctionne
curl http://localhost:8000/health
curl http://localhost:3000

# Créer l'archive pour serveur
tar --exclude='node_modules' \
--exclude='.git' \
--exclude='venv' \
--exclude='.env' \
--exclude='*.pyc' \
-czf workflow-manager-deploy.tar.gz workflow-manager/
3. Transfert Serveur
   bash# SCP vers serveur
   scp workflow-manager-deploy.tar.gz user@serveur-boulot:/opt/

# Ou via clé USB si pas de réseau
cp workflow-manager-deploy.tar.gz /media/usb/
4. Installation Serveur
   bash# Sur serveur
   ssh user@serveur-boulot

cd /opt
tar -xzf workflow-manager-deploy.tar.gz
cd workflow-manager

# Configuration
cp .env.example .env
nano .env
# Remplir: DB_PASSWORD, LLM keys, etc.

# Démarrage
docker-compose up -d

# Init Ollama (si local)
docker exec workflow-ollama ollama pull qwen2.5:7b

# Vérification
docker-compose ps
docker-compose logs -f
5. Accès Utilisateurs
   bash# Sur serveur, récupérer l'IP
   hostname -I
# Ex: 192.168.1.100

# Annoncer aux collègues:
# http://192.168.1.100:3000

📋 CHECKLIST DÉPLOIEMENT
Avant de Transférer

.env.example à jour avec toutes les variables
INSTALL.md complet et testé
docker-compose.yml fonctionnel localement
Tous les Dockerfiles buildent sans erreur
Schema SQL dans schema.sql
README clair
.gitignore contient .env

Sur le Serveur

Docker et Docker Compose installés
Ports 3000, 8000, 5432 disponibles
.env créé et rempli
Secrets générés (DB_PASSWORD, SECRET_KEY)
docker-compose up -d fonctionne
Ollama model téléchargé (si local)
Backend health check OK
Frontend accessible
Premier projet créé (test)
Backup script configuré


🎁 BONUS : Script d'Installation Automatique
scripts/install.sh
bash#!/bin/bash

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
    
    sed -i "s/CHANGE_ME_STRONG_PASSWORD/$DB_PASS/" .env
    sed -i "s/CHANGE_ME_GENERATE_RANDOM_KEY/$SECRET/" .env
    
    echo "✅ Configuration créée (.env)"
    echo "⚠️  Éditer .env pour configurer le LLM (OpenAI/Anthropic keys)"
    
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
sleep 10

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
echo "❌ Backend KO"
fi

if curl -f http://localhost:3000/health > /dev/null 2>&1; then
echo "✅ Frontend opérationnel"
else
echo "❌ Frontend KO"
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
Rendre exécutable :
bashchmod +x scripts/install.sh
Installation en une commande :
bash./scripts/install.sh

✅ RÉSUMÉ FINAL
Pour Toi (Dev)
bash# 1. Dev local
docker-compose up -d

# 2. Package
tar -czf deploy.tar.gz workflow-manager/

# 3. Transfert
scp deploy.tar.gz serveur:/opt/
Pour Admin Serveur Boulot
bash# 1. Extraction
tar -xzf deploy.tar.gz && cd workflow-manager

# 2. Configuration (JUSTE .env à éditer)
cp .env.example .env
nano .env  # Remplir DB_PASSWORD et LLM keys

# 3. Installation
./scripts/install.sh
# OU
docker-compose up -d
C'est tout ! Aucune installation système complexe.

Tu veux que je détaille un aspect spécifique (CI/CD, backup auto, monitoring, etc.) ?PNcree moi un document que je puisse utiliser dans claude code pour ce projetSpécification Technique Complète - Workflow Manager (Version Production-Ready)
📋 Vue d'Ensemble du Projet
Objectif
Créer une application web fullstack permettant de gérer, visualiser et interroger des workflows capturés par une extension browser, avec un système RAG (Retrieval-Augmented Generation) pour générer automatiquement de la documentation et répondre aux questions sur les processus métier.
Particularité : Application développée localement, déployable facilement sur serveur professionnel via Docker.
Architecture Technique
Extension Browser (JavaScript)
↓ HTTP POST JSON
Backend API (FastAPI + SQL pur + psycopg2)
↓
PostgreSQL + pgvector
↑
Frontend (Vue 3 + Vuexy)
Stack Technique

Backend : FastAPI, psycopg2 (SQL pur, pas d'ORM), Python 3.11+
Frontend : Vue 3 (Composition API), Vuexy Template, Pinia, Axios
Database : PostgreSQL 15+ avec extension pgvector
RAG : Haystack, Sentence-Transformers (embeddings locaux)
LLM : Ollama (local), OpenAI API, Anthropic Claude (configurables)
Déploiement : Docker + Docker Compose

Philosophie : Simplicité, Portabilité, Configuration via .env

🏗️ PHASE 1 : Infrastructure Backend + Docker (3-4 jours)
Objectifs

API REST FastAPI avec SQL pur
Docker Compose pour orchestration complète
Configuration 100% via .env
Déployable clé en main

Structure Complète du Projet
workflow-manager/
├── docker-compose.yml              # Orchestration services
├── .env.example                    # Template configuration
├── .env                            # Configuration (git-ignored)
├── .gitignore
├── README.md
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # Point d'entrée FastAPI
│   │   ├── config.py               # Configuration (env vars)
│   │   │
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── connection.py       # Pool psycopg2
│   │   │   ├── schema.sql          # CREATE TABLE
│   │   │   └── queries/
│   │   │       ├── __init__.py
│   │   │       ├── projects.py
│   │   │       ├── workflows.py
│   │   │       └── documents.py
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py             # Dependencies (DB session)
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── projects.py
│   │   │       ├── workflows.py
│   │   │       ├── documents.py
│   │   │       ├── rag.py
│   │   │       └── chat.py
│   │   │
│   │   ├── schemas/                # Pydantic validation
│   │   │   ├── __init__.py
│   │   │   ├── project.py
│   │   │   ├── workflow.py
│   │   │   ├── document.py
│   │   │   └── rag.py
│   │   │
│   │   └── services/               # Business logic
│   │       ├── __init__.py
│   │       ├── rag_service.py      # Haystack RAG
│   │       ├── document_generator.py
│   │       └── llm_factory.py      # Multi-provider LLM
│   │
│   └── tests/
│       └── test_api.py
│
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf                  # Nginx config pour prod
│   ├── package.json
│   ├── vite.config.js
│   ├── .env.example
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── router/
│       ├── stores/
│       ├── api/
│       ├── views/
│       ├── components/
│       └── composables/
│
├── nginx/                          # Reverse proxy (optionnel)
│   └── nginx.conf
│
├── scripts/
│   ├── install.sh                  # Installation automatique
│   ├── generate-secrets.sh         # Génération secrets
│   └── backup.sh                   # Backup DB
│
└── docs/
├── INSTALL.md                  # Guide installation serveur
├── QUICKSTART.md
└── DEVELOPMENT.md
docker-compose.yml
yamlversion: '3.8'

services:
# PostgreSQL + pgvector
postgres:
image: pgvector/pgvector:pg15
container_name: workflow-db
environment:
POSTGRES_DB: ${DB_NAME:-workflows_db}
POSTGRES_USER: ${DB_USER:-workflow_user}
POSTGRES_PASSWORD: ${DB_PASSWORD}
POSTGRES_HOST_AUTH_METHOD: scram-sha-256
ports:
- "${DB_PORT:-5432}:5432"
volumes:
- postgres_data:/var/lib/postgresql/data
- ./backend/app/db/schema.sql:/docker-entrypoint-initdb.d/01-schema.sql
healthcheck:
test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-workflow_user}"]
interval: 10s
timeout: 5s
retries: 5
restart: unless-stopped

# Backend FastAPI
backend:
build:
context: ./backend
dockerfile: Dockerfile
container_name: workflow-backend
environment:
DATABASE_URL: postgresql://${DB_USER:-workflow_user}:${DB_PASSWORD}@postgres:5432/${DB_NAME:-workflows_db}
PROJECT_NAME: ${PROJECT_NAME:-Workflow Manager}
DEBUG: ${DEBUG:-false}
API_V1_PREFIX: /api/v1
BACKEND_CORS_ORIGINS: ${FRONTEND_URL:-http://localhost:3000}

      # LLM Config
      DEFAULT_LLM_PROVIDER: ${DEFAULT_LLM_PROVIDER:-ollama}
      OLLAMA_BASE_URL: ${OLLAMA_BASE_URL:-http://ollama:11434}
      OLLAMA_MODEL: ${OLLAMA_MODEL:-llama3.2:3b}
      OPENAI_API_KEY: ${OPENAI_API_KEY:-}
      OPENAI_MODEL: ${OPENAI_MODEL:-gpt-4o-mini}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:-}
      ANTHROPIC_MODEL: ${ANTHROPIC_MODEL:-claude-sonnet-4-20250514}
      
      # RAG Config
      EMBEDDING_MODEL_NAME: ${EMBEDDING_MODEL_NAME:-sentence-transformers/all-MiniLM-L6-v2}
      CHUNK_SIZE: ${CHUNK_SIZE:-1000}
      CHUNK_OVERLAP: ${CHUNK_OVERLAP:-200}
    ports:
      - "${BACKEND_PORT:-8000}:8000"
    volumes:
      - model_cache:/root/.cache
    depends_on:
      postgres:
        condition: service_healthy
      ollama:
        condition: service_started
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

# Frontend Vue 3
frontend:
build:
context: ./frontend
dockerfile: Dockerfile
args:
VITE_API_BASE_URL: ${BACKEND_URL:-http://localhost:8000}
container_name: workflow-frontend
ports:
- "${FRONTEND_PORT:-3000}:80"
depends_on:
- backend
restart: unless-stopped

# Ollama (LLM local)
ollama:
image: ollama/ollama:latest
container_name: workflow-ollama
ports:
- "${OLLAMA_PORT:-11434}:11434"
volumes:
- ollama_data:/root/.ollama
environment:
- OLLAMA_KEEP_ALIVE=24h
restart: unless-stopped

volumes:
postgres_data:
ollama_data:
model_cache:

networks:
default:
name: workflow-network
.env.example
env# ==============================================================================
# WORKFLOW MANAGER - CONFIGURATION
# ==============================================================================
# Copier ce fichier vers .env et remplir les valeurs
# NE PAS COMMITER .env dans Git !

# ------------------------------------------------------------------------------
# DATABASE
# ------------------------------------------------------------------------------
DB_NAME=workflows_db
DB_USER=workflow_user
DB_PASSWORD=CHANGE_ME_STRONG_PASSWORD
DB_PORT=5432

# ------------------------------------------------------------------------------
# APPLICATION
# ------------------------------------------------------------------------------
PROJECT_NAME=Workflow Manager
DEBUG=false
BACKEND_PORT=8000
FRONTEND_PORT=3000
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000

# ------------------------------------------------------------------------------
# LLM PROVIDER (ollama | openai | anthropic)
# ------------------------------------------------------------------------------
DEFAULT_LLM_PROVIDER=ollama

# --- Ollama (Local - Gratuit) ---
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_PORT=11434
OLLAMA_MODEL=llama3.2:3b
# Autres modèles: qwen2.5:7b (meilleur RAG), mistral:7b (meilleur français)

# --- OpenAI (Cloud - optionnel) ---
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini

# --- Anthropic Claude (Cloud - optionnel) ---
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-sonnet-4-20250514

# ------------------------------------------------------------------------------
# RAG CONFIGURATION
# ------------------------------------------------------------------------------
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
RAG_TOP_K_DEFAULT=5

# ------------------------------------------------------------------------------
# SECURITY (Générer avec: openssl rand -hex 32)
# ------------------------------------------------------------------------------
SECRET_KEY=CHANGE_ME_GENERATE_RANDOM_KEY
Schéma de Base de Données
Fichier : backend/app/db/schema.sql
sql-- Extension pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Table projects
CREATE TABLE IF NOT EXISTS projects (
id SERIAL PRIMARY KEY,
name VARCHAR(255) NOT NULL,
description TEXT,
created_at TIMESTAMP DEFAULT NOW(),
updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_projects_name ON projects(name);

-- Table workflows
CREATE TABLE IF NOT EXISTS workflows (
id SERIAL PRIMARY KEY,
project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
name VARCHAR(255) NOT NULL,
description TEXT,
raw_data JSONB NOT NULL,
workflow_hash VARCHAR(64) NOT NULL,
url VARCHAR(500),
domain VARCHAR(255),
duration_ms INTEGER,
created_at TIMESTAMP DEFAULT NOW(),
updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_workflows_project ON workflows(project_id);
CREATE INDEX idx_workflows_hash ON workflows(project_id, workflow_hash);
CREATE INDEX idx_workflows_domain ON workflows(domain);

-- Table workflow_states
CREATE TABLE IF NOT EXISTS workflow_states (
id SERIAL PRIMARY KEY,
workflow_id INTEGER NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
state_type VARCHAR(20) NOT NULL,
state_data JSONB NOT NULL,
sequence_order INTEGER NOT NULL,
timestamp TIMESTAMP NOT NULL
);

CREATE INDEX idx_states_workflow ON workflow_states(workflow_id);

-- Table workflow_actions
CREATE TABLE IF NOT EXISTS workflow_actions (
id SERIAL PRIMARY KEY,
workflow_id INTEGER NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
action_type VARCHAR(50) NOT NULL,
action_data JSONB NOT NULL,
sequence_order INTEGER NOT NULL,
timestamp TIMESTAMP NOT NULL
);

CREATE INDEX idx_actions_workflow ON workflow_actions(workflow_id);

-- Table documents
CREATE TABLE IF NOT EXISTS documents (
id SERIAL PRIMARY KEY,
project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
workflow_id INTEGER REFERENCES workflows(id) ON DELETE SET NULL,
title VARCHAR(255) NOT NULL,
content TEXT NOT NULL,
content_type VARCHAR(50) NOT NULL,
status VARCHAR(20) NOT NULL DEFAULT 'draft',
is_indexed BOOLEAN DEFAULT FALSE,
metadata JSONB,
version INTEGER DEFAULT 1,
created_at TIMESTAMP DEFAULT NOW(),
updated_at TIMESTAMP DEFAULT NOW(),
validated_at TIMESTAMP,
last_indexed_at TIMESTAMP,
chunks_count INTEGER DEFAULT 0
);

CREATE INDEX idx_documents_project ON documents(project_id);
CREATE INDEX idx_documents_workflow ON documents(workflow_id);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_indexed ON documents(is_indexed);

-- Table document_versions
CREATE TABLE IF NOT EXISTS document_versions (
id SERIAL PRIMARY KEY,
document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
content TEXT NOT NULL,
version_number INTEGER NOT NULL,
change_summary TEXT,
created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_versions_document ON document_versions(document_id);

-- Table document_chunks
CREATE TABLE IF NOT EXISTS document_chunks (
id SERIAL PRIMARY KEY,
document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
chunk_text TEXT NOT NULL,
chunk_index INTEGER NOT NULL,
embedding vector(384),
metadata JSONB,
created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_chunks_document ON document_chunks(document_id);
CREATE INDEX idx_chunks_project ON document_chunks(project_id);

-- Index vectoriel HNSW pour recherche rapide
CREATE INDEX idx_chunks_embedding ON document_chunks
USING hnsw (embedding vector_cosine_ops);
backend/Dockerfile
dockerfileFROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
build-essential \
curl \
postgresql-client \
&& rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download embedding model at build time
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Copy application
COPY app/ ./app/

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
backend/requirements.txt
txt# API
fastapi==0.109.2
uvicorn[standard]==0.27.1
python-multipart==0.0.9

# Database
psycopg2-binary==2.9.9

# Utils
python-dotenv==1.0.1
httpx==0.26.0

# RAG avec Haystack
haystack-ai==2.0.1
pgvector-haystack==0.2.0
sentence-transformers==2.5.1

# LLM providers
ollama-haystack==0.0.8
openai==1.12.0
anthropic==0.18.0

# WebSocket
websockets==12.0

# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
backend/app/config.py
pythonfrom pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
# Database
DATABASE_URL: str

    # API
    PROJECT_NAME: str = "Workflow Manager"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000"
    
    # LLM
    DEFAULT_LLM_PROVIDER: str = "ollama"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"
    
    # RAG
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    RAG_TOP_K_DEFAULT: int = 5
    
    # Security
    SECRET_KEY: str = "change-me-in-production"
    
    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(',')]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
backend/app/main.py
pythonfrom fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1 import projects, workflows, documents, rag

app = FastAPI(
title=settings.PROJECT_NAME,
debug=settings.DEBUG,
openapi_url=f"{settings.API_V1_PREFIX}/openapi.json"
)

# CORS
app.add_middleware(
CORSMiddleware,
allow_origins=settings.cors_origins,
allow_credentials=True,
allow_methods=["*"],
allow_headers=["*"],
)

# Health check
@app.get("/health")
def health_check():
return {"status": "ok"}

# Include routers
app.include_router(projects.router, prefix=f"{settings.API_V1_PREFIX}/projects", tags=["projects"])
app.include_router(workflows.router, prefix=f"{settings.API_V1_PREFIX}/workflows", tags=["workflows"])
app.include_router(documents.router, prefix=f"{settings.API_V1_PREFIX}/documents", tags=["documents"])
app.include_router(rag.router, prefix=f"{settings.API_V1_PREFIX}/rag", tags=["rag"])

@app.get("/")
def root():
return {"message": "Workflow Manager API", "docs": f"{settings.API_V1_PREFIX}/docs"}
backend/app/db/connection.py
pythonimport psycopg2
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
from app.config import settings

# Pool de connexions
pool = SimpleConnectionPool(
minconn=1,
maxconn=20,
dsn=settings.DATABASE_URL
)

@contextmanager
def get_db():
"""Context manager pour connexion DB"""
conn = pool.getconn()
try:
yield conn
conn.commit()
except Exception:
conn.rollback()
raise
finally:
pool.putconn(conn)
frontend/Dockerfile
dockerfile# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

# Production stage
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
frontend/nginx.conf
nginxserver {
listen 80;
server_name _;

    root /usr/share/nginx/html;
    index index.html;

    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
scripts/install.sh
bash#!/bin/bash

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
docs/INSTALL.md
markdown# Installation Serveur - Workflow Manager

## Prérequis

- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 20GB espace disque

## Installation Rapide

### 1. Transférer les fichiers
```bash
# Sur ton PC local
tar -czf workflow-manager.tar.gz workflow-manager/
scp workflow-manager.tar.gz user@serveur:/opt/

# Sur le serveur
cd /opt
tar -xzf workflow-manager.tar.gz
cd workflow-manager
```

### 2. Installation automatique
```bash
chmod +x scripts/install.sh
./scripts/install.sh
```

Le script va :
- Créer le fichier .env avec secrets générés
- Builder les images Docker
- Démarrer tous les services
- Télécharger le modèle Ollama (si provider=ollama)

### 3. Configuration manuelle (si nécessaire)

Si vous voulez configurer manuellement :
```bash
cp .env.example .env
nano .env
```

**Configuration minimale requise :**
```env
# OBLIGATOIRE
DB_PASSWORD=votre_mot_de_passe_fort

# LLM Provider (choisir un)
DEFAULT_LLM_PROVIDER=ollama  # ou openai/anthropic

# Si OpenAI
OPENAI_API_KEY=sk-...

# Si Anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

Puis :
```bash
docker-compose up -d
```

## Vérification
```bash
# Statut services
docker-compose ps

# Backend
curl http://localhost:8000/health
# {"status":"ok"}

# Frontend
curl http://localhost:3000/health
# healthy

# Ollama (si local)
curl http://localhost:11434/api/tags
```

## Accès

- **Frontend** : http://serveur:3000
- **API Docs** : http://serveur:8000/docs
- **Ollama** : http://serveur:11434

## Maintenance

### Logs
```bash
docker-compose logs -f
docker-compose logs -f backend
```

### Redémarrage
```bash
docker-compose restart
```

### Mise à jour
```bash
docker-compose pull
docker-compose up -d --build
```

### Backup
```bash
# Backup DB
docker exec workflow-db pg_dump -U workflow_user workflows_db > backup-$(date +%Y%m%d).sql

# Restore
docker exec -i workflow-db psql -U workflow_user workflows_db < backup.sql
```

### Arrêt
```bash
docker-compose down
```

## Dépannage

### Ollama lent

CPU only est normal. Pour GPU :
```bash
# Vérifier GPU
nvidia-smi

# Décommenter dans docker-compose.yml la section GPU pour ollama
```

### Backend ne démarre pas
```bash
docker-compose logs backend
```

Vérifier DATABASE_URL dans .env

### Port déjà utilisé

Modifier dans .env :
```env
BACKEND_PORT=8001
FRONTEND_PORT=3001
```
README.md (racine)
markdown# Workflow Manager

Application web pour capturer, documenter et interroger des workflows métier via RAG/LLM.

## 🚀 Démarrage Rapide

### Développement Local
```bash
# 1. Copier configuration
cp .env.example .env

# 2. Lancer tout
docker-compose up -d

# 3. Accéder
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

### Installation Serveur

Voir [docs/INSTALL.md](docs/INSTALL.md)
```bash
./scripts/install.sh
```

## 📚 Documentation

- [Guide Installation](docs/INSTALL.md)
- [Guide Développement](docs/DEVELOPMENT.md)
- [API Documentation](http://localhost:8000/docs)

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
- **Frontend** : Vue 3, Vuexy
- **Database** : PostgreSQL 15 + pgvector
- **LLM** : Ollama (local) ou OpenAI/Anthropic (API)
- **Déploiement** : Docker Compose

## 🤝 Contribution

Développement :
```bash
# Mode dev avec hot reload
docker-compose -f docker-compose.dev.yml up
```

Tests :
```bash
# Backend
docker exec workflow-backend pytest

# Frontend
cd frontend && npm test
```

## 📄 License

MIT

🎯 PHASES DE DÉVELOPPEMENT
Les phases détaillées sont identiques à la spec précédente (Phase 1 à Phase 7), avec l'ajout de :
Considérations Docker pour Chaque Phase
Phase 1 : Backend

Créer Dockerfile backend
Créer docker-compose.yml
Tester build et run en local

Phase 2 : Frontend

Créer Dockerfile frontend
Ajouter service frontend au docker-compose
Tester communication backend ↔ frontend

Phase 3 : Sync Extension

Pas de changement Docker
Extension communique avec backend via URL configurable

Phase 4 : Documents

Pas de changement Docker
Nouvelles tables dans schema.sql

Phase 5 : RAG

Télécharger embedding model dans Dockerfile
Volume pour cache models
Tester indexation dans container

Phase 6 : LLM + Chat

Ajouter service Ollama au docker-compose
Tester multi-provider (Ollama/OpenAI/Anthropic)
WebSocket dans backend

Phase 7 : Finalisation

Script install.sh
Documentation INSTALL.md
Tests en conditions réelles (transfert → serveur)


✅ CHECKLIST DÉVELOPPEMENT
Setup Initial

Cloner/créer structure projet
Créer .env depuis .env.example
Lancer docker-compose up -d
Vérifier http://localhost:8000/docs accessible

Phase 1 - Backend

schema.sql avec toutes les tables
Endpoints CRUD projects
Endpoints CRUD workflows
Tests API avec pytest
Health check endpoint

Phase 2 - Frontend

Setup Vue 3 + Vuexy
Pages principales (Dashboard, Projects, Workflows)
Communication API fonctionnelle
Build Docker frontend OK

Phase 3 - Sync Extension

Endpoint import workflow
Détection doublons (hash)
Extension modifiée pour POST vers backend

Phase 4 - Documents

Tables documents + versions
CRUD documents
Génération basique (JSON → Markdown)
Versioning fonctionnel

Phase 5 - RAG

pgvector installé
Service Haystack RAG
Indexation documents
Recherche vectorielle

Phase 6 - LLM

Service multi-provider (Ollama/OpenAI/Anthropic)
RAG complet (retrieval + generation)
WebSocket chat
Génération doc par LLM

Phase 7 - Production

Script install.sh fonctionnel
Documentation INSTALL.md complète
Tests sur serveur réel
Backup script


🚀 COMMANDES UTILES
Développement
bash# Démarrer tout
docker-compose up -d

# Voir les logs
docker-compose logs -f

# Rebuild après modif
docker-compose up -d --build

# Arrêter tout
docker-compose down

# Supprimer volumes (DANGER: perte données)
docker-compose down -v
Tests
bash# Tests backend
docker exec workflow-backend pytest

# Shell dans container
docker exec -it workflow-backend bash

# Psql
docker exec -it workflow-db psql -U workflow_user workflows_db
Production
bash# Package pour serveur
tar --exclude='node_modules' --exclude='.git' --exclude='venv' --exclude='.env' -czf deploy.tar.gz workflow-manager/

# Sur serveur
./scripts/install.sh
