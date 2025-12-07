<template>
  <div class="documents-view">
    <div class="header">
      <h1>Documents</h1>
      <div class="actions">
        <button @click="fetchDocuments" class="btn btn-secondary">Refresh</button>
      </div>
    </div>

    <div v-if="loading" class="loading">Loading documents...</div>

    <div v-else-if="error" class="error">
      <p>Error loading documents: {{ error }}</p>
      <button @click="fetchDocuments" class="btn btn-primary">Retry</button>
    </div>

    <div v-else-if="documents.length === 0" class="empty">
      <p>No documents yet. Generate documents from your workflows.</p>
    </div>

    <div v-else class="documents-grid">
      <div
        v-for="doc in documents"
        :key="doc.id"
        class="document-card"
        :class="'status-' + doc.status"
      >
        <div class="document-header">
          <h3>{{ doc.title }}</h3>
          <span :class="'badge badge-' + doc.status">{{ doc.status }}</span>
        </div>

        <div class="document-meta">
          <div class="meta-item">
            <strong>Type:</strong> {{ doc.content_type }}
          </div>
          <div class="meta-item">
            <strong>Version:</strong> {{ doc.version }}
          </div>
          <div class="meta-item">
            <strong>Created:</strong> {{ formatDate(doc.created_at) }}
          </div>
          <div class="meta-item">
            <strong>Updated:</strong> {{ formatDate(doc.updated_at) }}
          </div>
        </div>

        <div class="document-actions">
          <button @click="viewDocument(doc.id)" class="btn btn-sm btn-primary">
            View
          </button>
          <button
            v-if="doc.status === 'draft'"
            @click="validateDocument(doc.id)"
            class="btn btn-sm btn-success"
          >
            Validate
          </button>
          <button
            v-if="doc.status === 'validated'"
            @click="publishDocument(doc.id)"
            class="btn btn-sm btn-info"
          >
            Publish
          </button>
          <button
            @click="viewVersions(doc.id)"
            class="btn btn-sm btn-secondary"
          >
            Versions ({{ doc.version }})
          </button>
        </div>
      </div>
    </div>

    <!-- Document Detail Modal -->
    <div v-if="selectedDocument" class="modal" @click.self="closeModal">
      <div class="modal-content">
        <div class="modal-header">
          <h2>{{ selectedDocument.title }}</h2>
          <button @click="closeModal" class="close-btn">&times;</button>
        </div>
        <div class="modal-body">
          <div class="document-info">
            <span :class="'badge badge-' + selectedDocument.status">
              {{ selectedDocument.status }}
            </span>
            <span class="version-badge">v{{ selectedDocument.version }}</span>
          </div>
          <div class="document-content">
            <pre v-if="selectedDocument.content_type === 'json'">{{ selectedDocument.content }}</pre>
            <div v-else v-html="renderMarkdown(selectedDocument.content)"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Versions Modal -->
    <div v-if="showVersions" class="modal" @click.self="closeVersionsModal">
      <div class="modal-content">
        <div class="modal-header">
          <h2>Document Versions</h2>
          <button @click="closeVersionsModal" class="close-btn">&times;</button>
        </div>
        <div class="modal-body">
          <div v-if="loadingVersions">Loading versions...</div>
          <div v-else class="versions-list">
            <div
              v-for="version in versions"
              :key="version.id"
              class="version-item"
            >
              <div class="version-header">
                <strong>Version {{ version.version_number }}</strong>
                <span class="version-date">{{ formatDate(version.created_at) }}</span>
              </div>
              <div class="version-summary">
                {{ version.change_summary || 'No summary' }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'

const documents = ref([])
const loading = ref(false)
const error = ref(null)
const selectedDocument = ref(null)
const showVersions = ref(false)
const versions = ref([])
const loadingVersions = ref(false)

const fetchDocuments = async () => {
  loading.value = true
  error.value = null
  try {
    const response = await axios.get(`${apiUrl}/api/v1/documents/`)
    documents.value = response.data
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

const viewDocument = async (docId) => {
  try {
    const response = await axios.get(`${apiUrl}/api/v1/documents/${docId}`)
    selectedDocument.value = response.data
  } catch (err) {
    error.value = err.message
  }
}

const closeModal = () => {
  selectedDocument.value = null
}

const validateDocument = async (docId) => {
  try {
    await axios.post(`${apiUrl}/api/v1/documents/${docId}/validate`)
    await fetchDocuments()
  } catch (err) {
    error.value = err.message
  }
}

const publishDocument = async (docId) => {
  try {
    await axios.post(`${apiUrl}/api/v1/documents/${docId}/publish`)
    await fetchDocuments()
  } catch (err) {
    error.value = err.message
  }
}

const viewVersions = async (docId) => {
  loadingVersions.value = true
  showVersions.value = true
  try {
    const response = await axios.get(`${apiUrl}/api/v1/documents/${docId}/versions`)
    versions.value = response.data
  } catch (err) {
    error.value = err.message
  } finally {
    loadingVersions.value = false
  }
}

const closeVersionsModal = () => {
  showVersions.value = false
  versions.value = []
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleString()
}

const renderMarkdown = (content) => {
  // Simple markdown to HTML (for production, use a proper library like marked.js)
  return content
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>')
    .replace(/\*(.*)\*/gim, '<em>$1</em>')
    .replace(/\n/gim, '<br>')
}

onMounted(() => {
  fetchDocuments()
})
</script>

<style scoped>
.documents-view {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.header h1 {
  margin: 0;
  font-size: 2rem;
  color: #333;
}

.actions {
  display: flex;
  gap: 1rem;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-primary:hover {
  background-color: #0056b3;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.btn-success {
  background-color: #28a745;
  color: white;
}

.btn-info {
  background-color: #17a2b8;
  color: white;
}

.btn-sm {
  padding: 0.25rem 0.75rem;
  font-size: 0.85rem;
}

.loading,
.error,
.empty {
  text-align: center;
  padding: 3rem;
  color: #666;
}

.error {
  color: #dc3545;
}

.documents-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
}

.document-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 1.5rem;
  background: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s;
}

.document-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.document-card.status-draft {
  border-left: 4px solid #ffc107;
}

.document-card.status-validated {
  border-left: 4px solid #28a745;
}

.document-card.status-published {
  border-left: 4px solid #007bff;
}

.document-header {
  display: flex;
  justify-content: space-between;
  align-items: start;
  margin-bottom: 1rem;
}

.document-header h3 {
  margin: 0;
  font-size: 1.2rem;
  color: #333;
  flex: 1;
}

.badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: bold;
  text-transform: uppercase;
}

.badge-draft {
  background-color: #fff3cd;
  color: #856404;
}

.badge-validated {
  background-color: #d4edda;
  color: #155724;
}

.badge-published {
  background-color: #d1ecf1;
  color: #0c5460;
}

.document-meta {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.5rem;
  margin-bottom: 1rem;
  font-size: 0.85rem;
  color: #666;
}

.document-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  max-width: 900px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #ddd;
}

.modal-header h2 {
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  font-size: 2rem;
  cursor: pointer;
  color: #666;
}

.modal-body {
  padding: 1.5rem;
}

.document-info {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.version-badge {
  padding: 0.25rem 0.75rem;
  background-color: #e9ecef;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: bold;
}

.document-content {
  background: #f8f9fa;
  padding: 1.5rem;
  border-radius: 4px;
  max-height: 60vh;
  overflow-y: auto;
}

.document-content pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
}

.versions-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.version-item {
  padding: 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.version-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.version-date {
  color: #666;
  font-size: 0.85rem;
}

.version-summary {
  color: #666;
  font-size: 0.9rem;
}
</style>
