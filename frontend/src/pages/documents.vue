<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

definePage({
  meta: {
    layout: 'default',
  },
})

const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'

const documents = ref([])
const loading = ref(false)
const detailsDialog = ref(false)
const versionsDialog = ref(false)
const selectedDocument = ref(null)
const versions = ref([])
const loadingVersions = ref(false)
const search = ref('')

const snackbar = ref(false)
const snackbarText = ref('')
const snackbarColor = ref('success')

const fetchDocuments = async () => {
  loading.value = true
  try {
    const response = await axios.get(`${apiUrl}/api/v1/documents/`)
    documents.value = response.data
  } catch (error) {
    showSnackbar('Erreur lors du chargement des documents', 'error')
    console.error('Error fetching documents:', error)
  } finally {
    loading.value = false
  }
}

const viewDocument = async (docId) => {
  try {
    const response = await axios.get(`${apiUrl}/api/v1/documents/${docId}`)
    selectedDocument.value = response.data
    detailsDialog.value = true
  } catch (error) {
    showSnackbar('Erreur lors du chargement du document', 'error')
    console.error('Error fetching document:', error)
  }
}

const validateDocument = async (docId) => {
  try {
    await axios.post(`${apiUrl}/api/v1/documents/${docId}/validate`)
    showSnackbar('Document validé avec succès', 'success')
    await fetchDocuments()
  } catch (error) {
    showSnackbar('Erreur lors de la validation du document', 'error')
    console.error('Error validating document:', error)
  }
}

const publishDocument = async (docId) => {
  try {
    await axios.post(`${apiUrl}/api/v1/documents/${docId}/publish`)
    showSnackbar('Document publié avec succès', 'success')
    await fetchDocuments()
  } catch (error) {
    showSnackbar('Erreur lors de la publication du document', 'error')
    console.error('Error publishing document:', error)
  }
}

const viewVersions = async (docId) => {
  loadingVersions.value = true
  versionsDialog.value = true
  try {
    const response = await axios.get(`${apiUrl}/api/v1/documents/${docId}/versions`)
    versions.value = response.data.sort((a, b) => b.version_number - a.version_number)
  } catch (error) {
    showSnackbar('Erreur lors du chargement des versions', 'error')
    console.error('Error fetching versions:', error)
  } finally {
    loadingVersions.value = false
  }
}

const indexDocument = async (docId) => {
  try {
    await axios.post(`${apiUrl}/api/v1/documents/${docId}/index`)
    showSnackbar('Document indexé avec succès', 'success')
    await fetchDocuments()
  } catch (error) {
    showSnackbar('Erreur lors de l\'indexation du document', 'error')
    console.error('Error indexing document:', error)
  }
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('fr-FR', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getStatusColor = (status) => {
  const colors = {
    'draft': 'warning',
    'validated': 'success',
    'published': 'primary'
  }
  return colors[status] || 'default'
}

const getStatusIcon = (status) => {
  const icons = {
    'draft': 'tabler-pencil',
    'validated': 'tabler-check',
    'published': 'tabler-send'
  }
  return icons[status] || 'tabler-file'
}

const renderMarkdown = (content) => {
  if (!content) return ''

  return content
    .replace(/^# (.*$)/gim, '<h1 class="text-h4 mb-4">$1</h1>')
    .replace(/^## (.*$)/gim, '<h2 class="text-h5 mb-3">$1</h2>')
    .replace(/^### (.*$)/gim, '<h3 class="text-h6 mb-2">$1</h3>')
    .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/gim, '<em>$1</em>')
    .replace(/`(.*?)`/gim, '<code class="px-1 py-05 bg-surface-variant rounded text-caption">$1</code>')
    .replace(/\n/gim, '<br>')
}

const showSnackbar = (text, color = 'success') => {
  snackbarText.value = text
  snackbarColor.value = color
  snackbar.value = true
}

onMounted(() => {
  fetchDocuments()
})
</script>

<template>
  <div>
    <!-- Header -->
    <div class="d-flex flex-wrap justify-space-between align-center gap-4 mb-6">
      <div>
        <h4 class="text-h4 mb-1">
          Documents
        </h4>
        <p class="text-body-1 mb-0">
          Documentation automatiquement générée depuis vos workflows
        </p>
      </div>
      <VBtn
        prepend-icon="tabler-refresh"
        variant="tonal"
        @click="fetchDocuments"
      >
        Actualiser
      </VBtn>
    </div>

    <!-- Empty State -->
    <VCard v-if="documents.length === 0 && !loading">
      <VCardText class="text-center pa-10">
        <VAvatar
          color="primary"
          variant="tonal"
          size="80"
          class="mb-4"
        >
          <VIcon
            icon="tabler-file-off"
            size="40"
          />
        </VAvatar>
        <h5 class="text-h5 mb-2">
          Aucun document
        </h5>
        <p class="text-body-1 mb-0">
          Générez des documents à partir de vos workflows pour commencer
        </p>
      </VCardText>
    </VCard>

    <!-- Documents Grid -->
    <VRow v-else>
      <VCol
        v-for="doc in documents"
        :key="doc.id"
        cols="12"
        md="6"
        lg="4"
      >
        <VCard
          class="document-card"
          :class="`status-${doc.status}`"
        >
          <VCardText>
            <div class="d-flex align-center justify-space-between mb-3">
              <VChip
                :color="getStatusColor(doc.status)"
                :prepend-icon="getStatusIcon(doc.status)"
                size="small"
                variant="tonal"
              >
                {{ doc.status }}
              </VChip>
              <VChip
                size="small"
                variant="outlined"
              >
                v{{ doc.version }}
              </VChip>
            </div>

            <h6 class="text-h6 mb-2">
              {{ doc.title }}
            </h6>

            <VList density="compact">
              <VListItem class="px-0">
                <template #prepend>
                  <VIcon
                    icon="tabler-file-type"
                    size="18"
                    class="me-2"
                  />
                </template>
                <VListItemTitle class="text-caption text-disabled">
                  Type
                </VListItemTitle>
                <VListItemSubtitle class="text-body-2">
                  {{ doc.content_type }}
                </VListItemSubtitle>
              </VListItem>

              <VListItem class="px-0">
                <template #prepend>
                  <VIcon
                    icon="tabler-calendar"
                    size="18"
                    class="me-2"
                  />
                </template>
                <VListItemTitle class="text-caption text-disabled">
                  Créé le
                </VListItemTitle>
                <VListItemSubtitle class="text-body-2">
                  {{ formatDate(doc.created_at) }}
                </VListItemSubtitle>
              </VListItem>
            </VList>

            <VDivider class="my-3" />

            <div class="d-flex flex-wrap gap-2">
              <VBtn
                size="small"
                variant="tonal"
                @click="viewDocument(doc.id)"
              >
                <VIcon
                  icon="tabler-eye"
                  start
                />
                Voir
              </VBtn>

              <VBtn
                v-if="doc.status === 'draft'"
                size="small"
                color="success"
                variant="tonal"
                @click="validateDocument(doc.id)"
              >
                <VIcon
                  icon="tabler-check"
                  start
                />
                Valider
              </VBtn>

              <VBtn
                v-if="doc.status === 'validated'"
                size="small"
                color="primary"
                variant="tonal"
                @click="publishDocument(doc.id)"
              >
                <VIcon
                  icon="tabler-send"
                  start
                />
                Publier
              </VBtn>

              <VBtn
                v-if="!doc.is_indexed"
                size="small"
                color="warning"
                variant="tonal"
                @click="indexDocument(doc.id)"
              >
                <VIcon
                  icon="tabler-database-import"
                  start
                />
                Indexer
              </VBtn>

              <VChip
                v-else
                color="success"
                size="small"
                variant="tonal"
              >
                <VIcon
                  icon="tabler-check"
                  start
                  size="16"
                />
                Indexé ({{ doc.chunks_count || 0 }})
              </VChip>

              <VBtn
                size="small"
                color="secondary"
                variant="tonal"
                @click="viewVersions(doc.id)"
              >
                <VIcon
                  icon="tabler-versions"
                  start
                />
                Versions
              </VBtn>
            </div>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>

    <!-- Document Details Dialog -->
    <VDialog
      v-model="detailsDialog"
      max-width="900"
      scrollable
    >
      <VCard v-if="selectedDocument">
        <VCardText>
          <VBtn
            icon
            size="x-small"
            color="default"
            variant="text"
            class="position-absolute"
            style="inset-block-start: 0.75rem; inset-inline-end: 0.75rem;"
            @click="detailsDialog = false"
          >
            <VIcon
              size="20"
              icon="tabler-x"
            />
          </VBtn>

          <div class="mb-6">
            <h5 class="text-h5 mb-2">
              {{ selectedDocument.title }}
            </h5>
            <div class="d-flex gap-2 flex-wrap">
              <VChip
                :color="getStatusColor(selectedDocument.status)"
                :prepend-icon="getStatusIcon(selectedDocument.status)"
                size="small"
                variant="tonal"
              >
                {{ selectedDocument.status }}
              </VChip>
              <VChip
                size="small"
                variant="outlined"
              >
                Version {{ selectedDocument.version }}
              </VChip>
              <VChip
                size="small"
                variant="outlined"
                prepend-icon="tabler-file-type"
              >
                {{ selectedDocument.content_type }}
              </VChip>
            </div>
          </div>

          <VDivider class="mb-4" />

          <div
            v-if="selectedDocument.content_type === 'json'"
            class="pa-4 bg-surface-variant rounded"
          >
            <pre class="text-caption overflow-auto">{{ selectedDocument.content }}</pre>
          </div>
          <div
            v-else
            class="pa-4 bg-surface-variant rounded markdown-content"
            v-html="renderMarkdown(selectedDocument.content)"
          />
        </VCardText>
      </VCard>
    </VDialog>

    <!-- Versions Dialog -->
    <VDialog
      v-model="versionsDialog"
      max-width="600"
      scrollable
    >
      <VCard>
        <VCardText>
          <VBtn
            icon
            size="x-small"
            color="default"
            variant="text"
            class="position-absolute"
            style="inset-block-start: 0.75rem; inset-inline-end: 0.75rem;"
            @click="versionsDialog = false"
          >
            <VIcon
              size="20"
              icon="tabler-x"
            />
          </VBtn>

          <div class="text-center mb-6">
            <VAvatar
              color="primary"
              variant="tonal"
              size="56"
              class="mb-3"
            >
              <VIcon
                icon="tabler-versions"
                size="28"
              />
            </VAvatar>
            <h5 class="text-h5 mb-1">
              Versions du Document
            </h5>
            <p class="text-body-2 text-disabled mb-0">
              Historique des modifications
            </p>
          </div>

          <VTimeline
            v-if="!loadingVersions && versions.length > 0"
            side="end"
            density="compact"
            truncate-line="both"
          >
            <VTimelineItem
              v-for="version in versions"
              :key="version.id"
              dot-color="primary"
              size="small"
            >
              <template #opposite>
                <div class="text-caption text-disabled">
                  {{ formatDate(version.created_at) }}
                </div>
              </template>
              <div>
                <div class="d-flex align-center gap-2 mb-1">
                  <VChip
                    color="primary"
                    size="x-small"
                    variant="tonal"
                  >
                    v{{ version.version_number }}
                  </VChip>
                </div>
                <p class="text-body-2 mb-0">
                  {{ version.change_summary || 'Aucun résumé' }}
                </p>
              </div>
            </VTimelineItem>
          </VTimeline>

          <div
            v-else-if="loadingVersions"
            class="text-center pa-10"
          >
            <VProgressCircular
              indeterminate
              color="primary"
            />
          </div>

          <VAlert
            v-else
            type="info"
            variant="tonal"
          >
            Aucune version disponible
          </VAlert>
        </VCardText>
      </VCard>
    </VDialog>

    <!-- Snackbar -->
    <VSnackbar
      v-model="snackbar"
      :color="snackbarColor"
      location="top end"
    >
      {{ snackbarText }}
    </VSnackbar>
  </div>
</template>

<style scoped>
.document-card {
  transition: transform 0.2s, box-shadow 0.2s;
  height: 100%;
}

.document-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 20px rgba(var(--v-theme-on-surface), 0.1);
}

.document-card.status-draft {
  border-left: 4px solid rgb(var(--v-theme-warning));
}

.document-card.status-validated {
  border-left: 4px solid rgb(var(--v-theme-success));
}

.document-card.status-published {
  border-left: 4px solid rgb(var(--v-theme-primary));
}

.markdown-content {
  line-height: 1.7;
}

.markdown-content h1,
.markdown-content h2,
.markdown-content h3 {
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
}

.markdown-content h1:first-child,
.markdown-content h2:first-child,
.markdown-content h3:first-child {
  margin-top: 0;
}

.markdown-content code {
  font-family: 'Courier New', monospace;
  font-size: 0.875em;
}

.markdown-content pre {
  overflow-x: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>
