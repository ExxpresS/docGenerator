# Installation Serveur - Workflow Manager

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
