-- Extension pgvector
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

-- Table rags (RAG collections)
CREATE TABLE IF NOT EXISTS rags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_rags_name ON rags(name);

-- Table uploaded_files (stores original uploaded files)
CREATE TABLE IF NOT EXISTS uploaded_files (
    id SERIAL PRIMARY KEY,
    rag_id INTEGER NOT NULL REFERENCES rags(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size INTEGER NOT NULL,
    file_content BYTEA NOT NULL,
    mime_type VARCHAR(100),
    uploaded_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

CREATE INDEX idx_uploaded_files_rag ON uploaded_files(rag_id);
CREATE INDEX idx_uploaded_files_type ON uploaded_files(file_type);

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
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    rag_id INTEGER REFERENCES rags(id) ON DELETE CASCADE,
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
    chunks_count INTEGER DEFAULT 0,
    CONSTRAINT doc_belongs_to_project_or_rag CHECK (
        (project_id IS NOT NULL AND rag_id IS NULL) OR
        (project_id IS NULL AND rag_id IS NOT NULL)
    )
);

CREATE INDEX idx_documents_project ON documents(project_id);
CREATE INDEX idx_documents_rag ON documents(rag_id);
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

-- Note: Table document_chunks is managed by Haystack PgvectorDocumentStore
-- Haystack will create its own table structure for storing documents and embeddings
-- The table will be created automatically when initializing the document store
-- Table name will be configured via HAYSTACK_TABLE_NAME in config
