<script setup>
import {useRouter} from "vue-router";
import {onMounted, ref} from "vue";
import axios from "axios";

definePage({
  meta: {
    layout: 'default',
  },
})

const router = useRouter()
const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'

const rags = ref([])
const loading = ref(false)
const dialog = ref(false)
const deleteDialog = ref(false)
const viewDialog = ref(false)
const editMode = ref(false)
const ragToDelete = ref(null)
const selectedRag = ref(null)
const selectedRagDocuments = ref([])
const selectedRagFiles = ref([])
const search = ref('')
const tab = ref('documents')

const snackbar = ref(false)
const snackbarText = ref('')
const snackbarColor = ref('success')

const formData = ref({
  name: '',
  description: ''
})

const headers = [
  { title: 'ID', key: 'id', sortable: true },
  { title: 'Nom', key: 'name', sortable: true },
  { title: 'Description', key: 'description', sortable: false },
  { title: 'Documents', key: 'document_count', sortable: true },
  { title: 'Fichiers', key: 'file_count', sortable: true },
  { title: 'Créé le', key: 'created_at', sortable: true },
  { title: 'Actions', key: 'actions', sortable: false, align: 'end' }
]

const fetchRAGs = async () => {
  loading.value = true
  try {
    const response = await axios.get(`${apiUrl}/api/v1/rags/`)

    const ragsWithStats = await Promise.all(
      response.data.map(async (rag) => {
        try {
          const statsResponse = await axios.get(`${apiUrl}/api/v1/rags/${rag.id}/stats`)
          return { ...rag, ...statsResponse.data }
        } catch (error) {
          return { ...rag, document_count: 0, file_count: 0 }
        }
      })
    )

    rags.value = ragsWithStats
  } catch (error) {
    showSnackbar('Erreur lors du chargement des RAGs', 'error')
    console.error('Error fetching RAGs:', error)
  } finally {
    loading.value = false
  }
}

const openCreateDialog = () => {
  editMode.value = false
  formData.value = { name: '', description: '' }
  dialog.value = true
}

const openEditDialog = (rag) => {
  editMode.value = true
  formData.value = {
    id: rag.id,
    name: rag.name,
    description: rag.description
  }
  dialog.value = true
}

const saveRAG = async () => {
  if (!formData.value.name) {
    showSnackbar('Le nom du RAG est requis', 'error')
    return
  }

  try {
    if (editMode.value) {
      await axios.put(`${apiUrl}/api/v1/rags/${formData.value.id}`, {
        name: formData.value.name,
        description: formData.value.description
      })
      showSnackbar('RAG modifié avec succès', 'success')
    } else {
      await axios.post(`${apiUrl}/api/v1/rags/`, {
        name: formData.value.name,
        description: formData.value.description
      })
      showSnackbar('RAG créé avec succès', 'success')
    }

    dialog.value = false
    await fetchRAGs()
  } catch (error) {
    showSnackbar('Erreur lors de la sauvegarde du RAG', 'error')
    console.error('Error saving RAG:', error)
  }
}

const confirmDelete = (rag) => {
  ragToDelete.value = rag
  deleteDialog.value = true
}

const deleteRAG = async () => {
  try {
    await axios.delete(`${apiUrl}/api/v1/rags/${ragToDelete.value.id}`)
    showSnackbar('RAG supprimé avec succès', 'success')
    deleteDialog.value = false
    await fetchRAGs()
  } catch (error) {
    showSnackbar('Erreur lors de la suppression du RAG', 'error')
    console.error('Error deleting RAG:', error)
  }
}

const viewRAG = async (rag) => {
  selectedRag.value = rag
  viewDialog.value = true

  try {
    const [docsResponse, filesResponse] = await Promise.all([
      axios.get(`${apiUrl}/api/v1/rags/${rag.id}/documents`),
      axios.get(`${apiUrl}/api/v1/rags/${rag.id}/files`)
    ])
    selectedRagDocuments.value = docsResponse.data
    selectedRagFiles.value = filesResponse.data
  } catch (error) {
    showSnackbar('Erreur lors du chargement des détails', 'error')
  }
}

const indexDocument = async (ragId, documentId) => {
  try {
    await axios.post(`${apiUrl}/api/v1/rags/${ragId}/documents/${documentId}/index`)
    showSnackbar('Document indexé avec succès', 'success')
    await viewRAG(selectedRag.value)
  } catch (error) {
    showSnackbar('Erreur lors de l\'indexation', 'error')
    console.error('Error indexing document:', error)
  }
}

const indexAllDocuments = async (ragId) => {
  try {
    const response = await axios.post(`${apiUrl}/api/v1/rags/${ragId}/index-all`)
    const successCount = response.data.results.filter(r => r.status === 'success').length
    showSnackbar(`${successCount} document(s) indexé(s)`, 'success')
    await viewRAG(selectedRag.value)
  } catch (error) {
    showSnackbar('Erreur lors de l\'indexation', 'error')
    console.error('Error indexing all documents:', error)
  }
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('fr-FR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

const formatFileSize = (bytes) => {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

const showSnackbar = (text, color = 'success') => {
  snackbarText.value = text
  snackbarColor.value = color
  snackbar.value = true
}

const handleRowClick = (event, row) => {
  router.push({ name: 'rags-id', params: { id: row.item.id } })
}

onMounted(() => {
  fetchRAGs()
})
</script>

<template>
  <div>
    <!-- Header -->
    <div class="d-flex flex-wrap justify-space-between align-center gap-4 mb-6">
      <div>
        <h4 class="text-h4 mb-1">
          RAG Collections
        </h4>
        <p class="text-body-1 mb-0">
          Gérez vos bases de connaissances pour la recherche sémantique
        </p>
      </div>
      <VBtn
        prepend-icon="tabler-plus"
        @click="openCreateDialog"
      >
        Nouveau RAG
      </VBtn>
    </div>

    <!-- RAGs Table Card -->
    <VCard>
      <VCardText class="d-flex align-center flex-wrap gap-4">
        <div class="me-3 d-flex gap-3">
          <VTextField
            v-model="search"
            prepend-inner-icon="tabler-search"
            placeholder="Rechercher un RAG..."
            density="compact"
            clearable
            hide-details
            style="min-inline-size: 250px;"
          />
        </div>
        <VSpacer />
        <div class="d-flex align-center gap-3">
          <VBtn
            icon
            variant="text"
            color="default"
            size="small"
            @click="fetchRAGs"
          >
            <VIcon icon="tabler-refresh" />
          </VBtn>
        </div>
      </VCardText>

      <VDivider />

      <VDataTable
        :headers="headers"
        :items="rags"
        :search="search"
        :loading="loading"
        :items-per-page="10"
        class="text-no-wrap clickable-rows"
        @click:row="handleRowClick"
      >
        <template #item.document_count="{ item }">
          <VChip
            color="primary"
            variant="tonal"
            size="small"
          >
            {{ item.document_count || 0 }}
          </VChip>
        </template>

        <template #item.file_count="{ item }">
          <VChip
            color="secondary"
            variant="tonal"
            size="small"
          >
            {{ item.file_count || 0 }}
          </VChip>
        </template>

        <template #item.created_at="{ item }">
          <span class="text-body-2">{{ formatDate(item.created_at) }}</span>
        </template>

        <template #item.actions="{ item }">
          <div class="d-flex gap-1">
            <VBtn
              icon
              variant="text"
              color="primary"
              size="small"
              @click="viewRAG(item)"
            >
              <VIcon icon="tabler-eye" />
              <VTooltip
                activator="parent"
                location="top"
              >
                Voir détails
              </VTooltip>
            </VBtn>
            <VBtn
              icon
              variant="text"
              color="default"
              size="small"
              @click="openEditDialog(item)"
            >
              <VIcon icon="tabler-edit" />
              <VTooltip
                activator="parent"
                location="top"
              >
                Modifier
              </VTooltip>
            </VBtn>
            <VBtn
              icon
              variant="text"
              color="error"
              size="small"
              @click="confirmDelete(item)"
            >
              <VIcon icon="tabler-trash" />
              <VTooltip
                activator="parent"
                location="top"
              >
                Supprimer
              </VTooltip>
            </VBtn>
          </div>
        </template>
      </VDataTable>
    </VCard>

    <!-- Create/Edit Dialog -->
    <VDialog
      v-model="dialog"
      max-width="600"
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
            @click="dialog = false"
          >
            <VIcon
              size="20"
              icon="tabler-x"
            />
          </VBtn>

          <div class="text-center mb-6">
            <h5 class="text-h5 mb-2">
              {{ editMode ? 'Modifier le RAG' : 'Nouveau RAG' }}
            </h5>
            <p class="text-body-1">
              {{ editMode ? 'Mettez à jour les informations du RAG' : 'Créez une nouvelle base de connaissances' }}
            </p>
          </div>

          <VForm @submit.prevent="saveRAG">
            <VRow>
              <VCol cols="12">
                <VTextField
                  v-model="formData.name"
                  label="Nom du RAG"
                  placeholder="Ma base de connaissances"
                  required
                />
              </VCol>

              <VCol cols="12">
                <VTextarea
                  v-model="formData.description"
                  label="Description"
                  placeholder="Description de la base de connaissances..."
                  rows="3"
                />
              </VCol>

              <VCol cols="6">
                <VBtn
                  color="secondary"
                  variant="tonal"
                  block
                  @click="dialog = false"
                >
                  Annuler
                </VBtn>
              </VCol>
              <VCol cols="6">
                <VBtn
                  type="submit"
                  block
                >
                  {{ editMode ? 'Modifier' : 'Créer' }}
                </VBtn>
              </VCol>
            </VRow>
          </VForm>
        </VCardText>
      </VCard>
    </VDialog>

    <!-- View RAG Details Dialog -->
    <VDialog
      v-model="viewDialog"
      max-width="900"
      scrollable
    >
      <VCard v-if="selectedRag">
        <VCardText>
          <VBtn
            icon
            size="x-small"
            color="default"
            variant="text"
            class="position-absolute"
            style="inset-block-start: 0.75rem; inset-inline-end: 0.75rem;"
            @click="viewDialog = false"
          >
            <VIcon
              size="20"
              icon="tabler-x"
            />
          </VBtn>

          <div class="mb-6">
            <h5 class="text-h5 mb-2">
              {{ selectedRag.name }}
            </h5>
            <p class="text-body-1">
              {{ selectedRag.description || 'Aucune description' }}
            </p>

            <div class="d-flex gap-2 mt-4">
              <VBtn
                size="small"
                color="primary"
                @click="indexAllDocuments(selectedRag.id)"
              >
                <VIcon
                  icon="tabler-database-import"
                  start
                />
                Indexer tout
              </VBtn>
            </div>
          </div>

          <VTabs
            v-model="tab"
            class="mb-4"
          >
            <VTab value="documents">
              Documents ({{ selectedRagDocuments.length }})
            </VTab>
            <VTab value="files">
              Fichiers ({{ selectedRagFiles.length }})
            </VTab>
          </VTabs>

          <VWindow v-model="tab">
            <VWindowItem value="documents">
              <VList v-if="selectedRagDocuments.length > 0">
                <VListItem
                  v-for="doc in selectedRagDocuments"
                  :key="doc.id"
                  class="mb-2"
                >
                  <template #prepend>
                    <VIcon
                      :icon="doc.is_indexed ? 'tabler-circle-check' : 'tabler-circle'"
                      :color="doc.is_indexed ? 'success' : 'default'"
                    />
                  </template>
                  <VListItemTitle>{{ doc.title }}</VListItemTitle>
                  <VListItemSubtitle>
                    {{ doc.chunks_count || 0 }} chunks | {{ doc.content_type }}
                  </VListItemSubtitle>
                  <template #append>
                    <VBtn
                      v-if="!doc.is_indexed"
                      size="small"
                      color="primary"
                      variant="tonal"
                      @click="indexDocument(selectedRag.id, doc.id)"
                    >
                      Indexer
                    </VBtn>
                    <VChip
                      v-else
                      color="success"
                      size="small"
                      variant="tonal"
                    >
                      Indexé
                    </VChip>
                  </template>
                </VListItem>
              </VList>
              <div
                v-else
                class="text-center pa-8 text-disabled"
              >
                <VIcon
                  icon="tabler-folder-open"
                  size="48"
                  class="mb-2"
                />
                <p>Aucun document</p>
              </div>
            </VWindowItem>

            <VWindowItem value="files">
              <VList v-if="selectedRagFiles.length > 0">
                <VListItem
                  v-for="file in selectedRagFiles"
                  :key="file.id"
                  class="mb-2"
                >
                  <template #prepend>
                    <VIcon icon="tabler-file" />
                  </template>
                  <VListItemTitle>{{ file.filename }}</VListItemTitle>
                  <VListItemSubtitle>
                    {{ formatFileSize(file.file_size) }} | {{ file.file_type }} | {{ formatDate(file.uploaded_at) }}
                  </VListItemSubtitle>
                </VListItem>
              </VList>
              <div
                v-else
                class="text-center pa-8 text-disabled"
              >
                <VIcon
                  icon="tabler-file-off"
                  size="48"
                  class="mb-2"
                />
                <p>Aucun fichier</p>
              </div>
            </VWindowItem>
          </VWindow>
        </VCardText>
      </VCard>
    </VDialog>

    <!-- Delete Dialog -->
    <VDialog
      v-model="deleteDialog"
      max-width="500"
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
            @click="deleteDialog = false"
          >
            <VIcon
              size="20"
              icon="tabler-x"
            />
          </VBtn>

          <div class="text-center mb-6">
            <VAvatar
              color="error"
              variant="tonal"
              size="64"
              class="mb-4"
            >
              <VIcon
                icon="tabler-trash"
                size="32"
              />
            </VAvatar>

            <h5 class="text-h5 mb-2">
              Confirmer la suppression
            </h5>
            <p class="text-body-1 mb-0">
              Êtes-vous sûr de vouloir supprimer le RAG <strong>"{{ ragToDelete?.name }}"</strong> ?
            </p>
          </div>

          <VRow>
            <VCol cols="6">
              <VBtn
                color="secondary"
                variant="tonal"
                block
                @click="deleteDialog = false"
              >
                Annuler
              </VBtn>
            </VCol>
            <VCol cols="6">
              <VBtn
                color="error"
                block
                @click="deleteRAG"
              >
                Supprimer
              </VBtn>
            </VCol>
          </VRow>
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
