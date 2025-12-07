# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Workflow Manager** is a fullstack web application for capturing, documenting, and querying business workflows using RAG (Retrieval-Augmented Generation). It allows users to capture workflows via a browser extension, automatically generate documentation, and interrogate the knowledge base using LLMs.

**Key Philosophy**: Simplicity, portability, 100% configuration via `.env`, deployable anywhere via Docker.

## Architecture

```
Browser Extension → Backend (FastAPI + Pure SQL) → PostgreSQL + pgvector
                         ↓
                    Frontend (Vue 3)
                         ↓
                    LLM (Ollama/OpenAI/Claude)
```

### Tech Stack
- **Backend**: FastAPI, psycopg2 (pure SQL, NO ORM), Python 3.11+
- **Frontend**: Vue 3 Composition API, Vite, Axios
- **Database**: PostgreSQL 15 + pgvector extension
- **LLM**: Multi-provider (Ollama local, OpenAI, Anthropic Claude)
- **Deployment**: Docker Compose

### Current Development Status
- ✅ **Phase 1**: Backend infrastructure (Projects, Workflows CRUD)
- ✅ **Phase 2**: Documents & Versioning (Document generation, workflow status management)
- ✅ **Phase 3**: Browser Extension (Workflow capture and sync)
- 🔄 **Phase 4-7**: RAG implementation, LLM integration, chat interface (planned)

## Development Commands

### Initial Setup
```bash
# Copy environment configuration
cp .env.example .env

# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps
curl http://localhost:8001/health  # Backend (note: port 8001, not 8000)
curl http://localhost:3001/health  # Frontend (note: port 3001, not 3000)
```

**Note**: Default ports have been changed to avoid conflicts:
- Backend: `8001` (not 8000)
- Frontend: `3001` (not 3000)
- Database: `5433` (not 5432)

### Working with Docker

```bash
# Rebuild after backend code changes
docker compose up -d --build backend

# Rebuild after frontend code changes
docker compose up -d --build frontend

# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Restart specific service
docker compose restart backend

# Stop all services
docker compose down

# Stop and remove volumes (WARNING: data loss)
docker compose down -v
```

### Database Operations

```bash
# Access PostgreSQL shell
docker exec -it workflow-db psql -U workflow_user workflows_db

# Backup database
docker exec workflow-db pg_dump -U workflow_user workflows_db > backup-$(date +%Y%m%d).sql

# Restore database
docker exec -i workflow-db psql -U workflow_user workflows_db < backup.sql
```

### Testing

```bash
# Backend tests
docker exec workflow-backend pytest

# Shell access to backend container
docker exec -it workflow-backend bash

# Shell access to database container
docker exec -it workflow-db bash
```

### Ollama (Local LLM)

```bash
# Download a model
docker exec workflow-ollama ollama pull llama3.2:3b

# List installed models
docker exec workflow-ollama ollama list

# Test Ollama API
curl http://localhost:11434/api/tags
```

## Code Architecture

### Backend Structure

**Key Pattern**: Pure SQL with psycopg2, NO ORM (SQLAlchemy/Tortoise not used).

```
backend/app/
├── main.py                 # FastAPI app entry point, router registration
├── config.py               # pydantic-settings for env vars
├── db/
│   ├── connection.py       # psycopg2 connection pooling with context managers
│   ├── schema.sql          # All table definitions (auto-loaded on DB init)
│   └── queries/            # Pure SQL query functions (one file per entity)
│       ├── projects.py
│       ├── workflows.py
│       └── documents.py
├── api/v1/                 # FastAPI routers
│   ├── projects.py
│   ├── workflows.py
│   └── documents.py
├── schemas/                # Pydantic models for validation
│   ├── project.py
│   ├── workflow.py
│   └── document.py
└── services/               # Business logic layer
    ├── document_generator.py  # JSON → Markdown conversion
    └── (future: rag_service.py, llm_factory.py)
```

### Database Connection Pattern

**Critical**: Always use context managers from `backend/app/db/connection.py`:

```python
from app.db.connection import get_cursor

# For SELECT/INSERT/UPDATE/DELETE
def my_query():
    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM table WHERE id = %s", (id,))
        return dict(cursor.fetchone())  # RealDictCursor returns dicts
```

**Connection Pooling**: Uses `SimpleConnectionPool` (1-20 connections). The pool is initialized lazily on first use.

**Transaction Handling**:
- `get_cursor()` automatically commits on success, rolls back on exception
- Multi-operation transactions stay within single `with get_cursor()` block
- Example: Document creation + version insertion use same cursor

### API Endpoint Pattern

Standard FastAPI router structure in `backend/app/api/v1/`:

```python
from fastapi import APIRouter, HTTPException, status
from app.schemas.entity import EntityCreate, Entity
from app.db.queries import entities

router = APIRouter()

@router.post("/", response_model=Entity, status_code=status.HTTP_201_CREATED)
def create_entity(entity: EntityCreate):
    try:
        db_entity = entities.create_entity(...)
        return db_entity
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Registration**: All routers are registered in `backend/app/main.py`:
```python
app.include_router(documents.router, prefix=f"{settings.API_V1_PREFIX}/documents", tags=["documents"])
```

### Database Schema

**Key Tables**:
- `projects`: Top-level organization
- `workflows`: Captured workflows with states and actions
- `workflow_states`, `workflow_actions`: Workflow step details (JSONB data)
- `documents`: Generated documentation with versioning
- `document_versions`: Full version history
- `document_chunks`: RAG chunks with pgvector embeddings (384-dim)

**Important Indexes**:
- `idx_chunks_embedding`: HNSW index on `document_chunks.embedding` for fast vector search
- `idx_workflows_hash`: Composite index for duplicate detection

### Document Generation

Documents are auto-generated from workflows using the `DocumentGenerator` service:

```python
from app.services.document_generator import DocumentGenerator

# Generate from workflow
doc = DocumentGenerator.generate_document_from_workflow(
    workflow_id=1,
    content_type="markdown",  # or "json"
    auto_validate=False
)
```

**Workflow to Markdown**: The generator creates structured documentation with:
- Metadata section (URL, domain, duration, captured date)
- Overview statistics
- States section (chronological)
- Actions section (chronological)
- Raw data appendix

### Document Versioning

**Status Workflow**: `draft` → `validated` → `published`

**Version Management**:
- Version is auto-incremented on content changes
- Each version is stored in `document_versions` table
- Versions are created in same transaction as document update
- Initial version (v1) is auto-created on document creation

### Frontend Structure

Vue 3 with Composition API:

```
frontend/src/
├── main.js              # App entry, Pinia, router setup
├── App.vue              # Root component with nav
├── router/index.js      # Vue Router routes
├── views/               # Page components
│   ├── Dashboard.vue
│   ├── Projects.vue
│   └── Documents.vue    # Full document management UI
└── (future: stores/, components/, composables/)
```

**API Integration**: All views use axios directly:
```javascript
const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'
const response = await axios.get(`${apiUrl}/api/v1/documents/`)
```

### Browser Extension Structure

Chrome/Firefox extension for capturing workflows from web pages:

```
extension/
├── manifest.json       # Extension configuration (manifest v3)
├── background.js       # Service worker (workflow state management)
├── content.js          # Content script (event capture on web pages)
├── popup.html          # Extension popup UI
├── popup.css           # Popup styles
├── popup.js            # Popup logic and API communication
└── icons/              # Extension icons (16x16, 48x48, 128x128)
```

**Key Components**:

- **background.js**: Manages recording state, workflow data structure, generates hash, syncs to API
- **content.js**: Injected into web pages to capture clicks, inputs, form submissions, navigation
- **popup.js**: UI for starting/stopping recording, configuring API endpoint, syncing workflows

**Event Capture**:
- Clicks: Element tag, id, classes, text, href, xpath
- Inputs: Field metadata (values redacted for security)
- Form submissions: Form action, method, field count
- Navigation: Page views, URL changes

**Workflow Hash**: Generated from URL + domain + action types + state types for duplicate detection

**Loading Extension**:
```bash
# Chrome/Edge
1. Go to chrome://extensions/
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select extension/ directory

# Firefox
1. Go to about:debugging#/runtime/this-firefox
2. Click "Load Temporary Add-on"
3. Select manifest.json from extension/ directory
```

**Extension Settings**: Stored in Chrome sync storage
- API URL (default: http://localhost:8001/api/v1)
- Project ID (must exist in backend)

## Configuration

**All configuration is via `.env` file**. Never hardcode values.

### Essential Environment Variables

```env
# Database (REQUIRED)
DB_PASSWORD=<generate with: openssl rand -hex 16>
DATABASE_URL=postgresql://workflow_user:${DB_PASSWORD}@postgres:5432/workflows_db

# Ports (adjust if conflicts)
BACKEND_PORT=8001
FRONTEND_PORT=3001
DB_PORT=5433

# LLM Provider (choose one)
DEFAULT_LLM_PROVIDER=ollama  # or "openai" or "anthropic"

# If using Ollama (local, free)
OLLAMA_MODEL=llama3.2:3b  # or qwen2.5:7b, mistral:7b

# If using OpenAI
OPENAI_API_KEY=sk-...

# If using Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Security
SECRET_KEY=<generate with: openssl rand -hex 32>
```

### Generating Secrets

```bash
# Database password (hex, no special chars)
openssl rand -hex 16

# Secret key
openssl rand -hex 32
```

## Important Patterns & Conventions

### Adding a New Entity/Resource

1. **Define schema** in `backend/app/db/schema.sql` (will be auto-loaded)
2. **Create Pydantic models** in `backend/app/schemas/entity.py`
3. **Write SQL queries** in `backend/app/db/queries/entity.py` using `get_cursor()`
4. **Create API router** in `backend/app/api/v1/entity.py`
5. **Register router** in `backend/app/main.py`
6. **Rebuild backend**: `docker compose up -d --build backend`

### Database Migrations

**Currently**: Schema changes require rebuilding the database.

```bash
# Update backend/app/db/schema.sql
# Recreate database (WARNING: data loss)
docker compose down -v
docker compose up -d
```

**For production**: Schema changes should be done via SQL migrations, not schema.sql rebuild.

### Password Handling in .env

**Critical**: Use hex encoding for database passwords, NOT base64.

```bash
# ✅ GOOD (hex - no special chars)
DB_PASSWORD=$(openssl rand -hex 16)

# ❌ BAD (base64 - may contain / or + causing parsing issues)
DB_PASSWORD=$(openssl rand -base64 32)
```

Special characters in passwords can break `DATABASE_URL` parsing in docker-compose.

### Transaction Patterns for Multi-Step Operations

When creating related records, keep them in same transaction:

```python
def create_document(...):
    with get_cursor() as cursor:
        # Insert parent record
        cursor.execute("INSERT INTO documents (...) RETURNING *")
        doc = dict(cursor.fetchone())

        # Insert child record in SAME transaction
        cursor.execute("INSERT INTO document_versions (...)")

        return doc
    # Auto-commit happens here
```

## API Documentation

**Interactive API docs**: http://localhost:8001/docs (Swagger UI)

**Current Endpoints** (Phase 1-2):
- `/api/v1/projects/*` - Project CRUD
- `/api/v1/workflows/*` - Workflow CRUD with duplicate detection
- `/api/v1/documents/*` - Document CRUD, generation, versioning, status workflow

**Health Checks**:
- Backend: `GET /health` → `{"status": "ok"}`
- Frontend: `GET /health` → `"healthy"`

## Troubleshooting

### Port Already Allocated

If you see "port is already allocated" errors:

1. Check current ports in `.env`:
```env
BACKEND_PORT=8001
FRONTEND_PORT=3001
DB_PORT=5433
```

2. Or change to different ports:
```bash
# Edit .env
BACKEND_PORT=8002
FRONTEND_PORT=3002

# Restart
docker compose down
docker compose up -d
```

### Database Password Authentication Failed

If you get "password authentication failed":

```bash
# 1. Generate new hex password
DB_PASSWORD=$(openssl rand -hex 16)

# 2. Update .env with new password

# 3. Recreate database volumes
docker compose down -v
docker compose up -d
```

### Backend Code Changes Not Reflected

**The backend code is NOT mounted as a volume** - you must rebuild:

```bash
docker compose up -d --build backend
```

### Frontend Code Changes Not Reflected

Frontend is built into the image:

```bash
docker compose up -d --build frontend
```

## Production Deployment

See `docs/INSTALL.md` for complete server installation guide.

**Quick deployment**:
```bash
# On server
./scripts/install.sh
```

The install script will:
- Generate secure passwords
- Build Docker images
- Start all services
- Download Ollama model (if using local LLM)
- Verify health checks

## Future Development Phases

Based on `specification.md`:

- ~~**Phase 3**: Browser extension sync~~ ✅ **COMPLETE**
- **Phase 4**: Document chunks and embeddings (pgvector integration)
- **Phase 5**: RAG implementation with Haystack + pgvector (indexing, retrieval)
- **Phase 6**: LLM integration (multi-provider chat with WebSocket)
- **Phase 7**: Production hardening, monitoring, backups

## Key Files to Reference

- `specification.md` - Complete project specification and requirements
- `backend/app/db/schema.sql` - Full database schema with all tables
- `backend/app/config.py` - All environment variables and their defaults
- `.env.example` - Template for environment configuration
- `docs/INSTALL.md` - Server installation and deployment guide
- `extension/README.md` - Browser extension installation and usage guide
