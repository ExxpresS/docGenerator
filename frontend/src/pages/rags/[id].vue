<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import TiptapEditor from '@core/components/TiptapEditor.vue'

definePage({
  meta: {
    layout: 'default',
  },
})

const route = useRoute()
const ragId = route.params.id

const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'

// State
const rag = ref(null)
const documents = ref([])
const selectedDocument = ref(null)
const editorContent = ref('')
const editMode = ref(false)
const loading = ref(false)
const createDialog = ref(false)
const newDocTitle = ref('')

// Fetch RAG details
const fetchRAG = async () => {
  try {
    const response = await axios.get(`${apiUrl}/api/v1/rags/${ragId}`)
    rag.value = response.data
  } catch (error) {
    console.error('Error fetching RAG:', error)
  }
}

// Fetch documents
const fetchDocuments = async () => {
  loading.value = true
  try {
    const response = await axios.get(`${apiUrl}/api/v1/rags/${ragId}/documents`)
    documents.value = response.data
  } catch (error) {
    console.error('Error fetching documents:', error)
  } finally {
    loading.value = false
  }
}

// Select document
const selectDocument = (doc) => {
  selectedDocument.value = doc
  editorContent.value = doc.content
  editMode.value = false
}

// Create new document
const createDocument = async () => {
  if (!newDocTitle.value.trim()) return

  try {
    const response = await axios.post(`${apiUrl}/api/v1/rags/${ragId}/documents`, {
      title: newDocTitle.value,
      content: '<p>Nouveau document</p>',
      content_type: 'html',
      status: 'draft'
    })

    documents.value.unshift(response.data)
    selectedDocument.value = response.data
    editorContent.value = response.data.content
    editMode.value = true
    createDialog.value = false
    newDocTitle.value = ''
  } catch (error) {
    console.error('Error creating document:', error)
  }
}

// Save document
const saveDocument = async () => {
  if (!selectedDocument.value) return

  try {
    const response = await axios.put(
      `${apiUrl}/api/v1/documents/${selectedDocument.value.id}`,
      {
        title: selectedDocument.value.title,
        content: editorContent.value,
        content_type: 'html'
      }
    )

    // Update document in list
    const index = documents.value.findIndex(d => d.id === selectedDocument.value.id)
    if (index !== -1) {
      documents.value[index] = response.data
      selectedDocument.value = response.data
    }

    editMode.value = false
  } catch (error) {
    console.error('Error saving document:', error)
  }
}

// Index document
const indexDocument = async (docId) => {
  try {
    await axios.post(`${apiUrl}/api/v1/documents/${docId}/index`)
    await fetchDocuments() // Refresh to show indexed status
  } catch (error) {
    console.error('Error indexing document:', error)
  }
}

onMounted(() => {
  fetchRAG()
  fetchDocuments()
})
</script>

<template>
  <div>
    <!-- Header -->
    <VCard class="mb-6">
      <VCardText>
        <div class="d-flex justify-space-between align-center">
          <div>
            <h2 class="text-h4 mb-2">
              {{ rag?.name || 'RAG' }}
            </h2>
            <p class="text-body-1 text-medium-emphasis">
              {{ rag?.description || 'Aucune description' }}
            </p>
          </div>
          <VBtn
            color="primary"
            @click="createDialog = true"
          >
            <VIcon
              start
              icon="tabler-plus"
            />
            Nouveau document
          </VBtn>
        </div>
      </VCardText>
    </VCard>

    <!-- Main content -->
    <VRow>
      <!-- Documents list -->
      <VCol cols="12" md="4">
        <VCard>
          <VCardTitle>Documents</VCardTitle>
          <VCardText>
            <VList>
              <VListItem
                v-for="doc in documents"
                :key="doc.id"
                :active="selectedDocument?.id === doc.id"
                @click="selectDocument(doc)"
                class="cursor-pointer"
              >
                <VListItemTitle>{{ doc.title }}</VListItemTitle>
                <VListItemSubtitle>
                  <VChip
                    size="x-small"
                    :color="doc.is_indexed ? 'success' : 'warning'"
                    class="mt-1"
                  >
                    {{ doc.is_indexed ? 'Indexé' : 'Non indexé' }}
                  </VChip>
                  <VChip
                    size="x-small"
                    :color="doc.status === 'published' ? 'success' : 'default'"
                    class="mt-1 ml-1"
                  >
                    {{ doc.status }}
                  </VChip>
                </VListItemSubtitle>
                <template v-slot:append>
                  <VBtn
                    v-if="!doc.is_indexed"
                    icon
                    size="x-small"
                    variant="text"
                    @click.stop="indexDocument(doc.id)"
                  >
                    <VIcon icon="tabler-database-import" />
                  </VBtn>
                </template>
              </VListItem>
            </VList>
            <div
              v-if="documents.length === 0 && !loading"
              class="text-center text-medium-emphasis pa-4"
            >
              Aucun document
            </div>
            <div
              v-if="loading"
              class="text-center pa-4"
            >
              <VProgressCircular indeterminate />
            </div>
          </VCardText>
        </VCard>
      </VCol>

      <!-- Editor -->
      <VCol cols="12" md="8">
        <VCard v-if="selectedDocument">
          <VCardTitle>
            <div class="d-flex justify-space-between align-center">
              <span>{{ selectedDocument.title }}</span>
              <div>
                <VBtn
                  v-if="!editMode"
                  color="primary"
                  variant="tonal"
                  @click="editMode = true"
                  class="mr-2"
                >
                  <VIcon
                    start
                    icon="tabler-edit"
                  />
                  Éditer
                </VBtn>
                <VBtn
                  v-if="editMode"
                  color="success"
                  @click="saveDocument"
                  class="mr-2"
                >
                  <VIcon
                    start
                    icon="tabler-device-floppy"
                  />
                  Sauvegarder
                </VBtn>
                <VBtn
                  v-if="editMode"
                  color="secondary"
                  variant="tonal"
                  @click="editMode = false; editorContent = selectedDocument.content"
                >
                  Annuler
                </VBtn>
              </div>
            </div>
          </VCardTitle>
          <VCardText>
            <TiptapEditor
              v-if="editMode"
              v-model="editorContent"
              placeholder="Commencez à écrire..."
            />
            <div
              v-else
              class="pa-4"
              v-html="editorContent"
            />
          </VCardText>
        </VCard>

        <VCard v-else>
          <VCardText class="text-center text-medium-emphasis pa-8">
            <VIcon
              icon="tabler-file-text"
              size="64"
              class="mb-4"
            />
            <p class="text-h6">
              Sélectionnez un document pour commencer
            </p>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>

    <!-- Create document dialog -->
    <VDialog
      v-model="createDialog"
      max-width="500"
    >
      <VCard>
        <VCardTitle>Nouveau document</VCardTitle>
        <VCardText>
          <VForm @submit.prevent="createDocument">
            <VTextField
              v-model="newDocTitle"
              label="Titre du document"
              placeholder="Mon document"
              autofocus
            />
          </VForm>
        </VCardText>
        <VCardActions>
          <VSpacer />
          <VBtn
            color="secondary"
            variant="tonal"
            @click="createDialog = false"
          >
            Annuler
          </VBtn>
          <VBtn
            color="primary"
            @click="createDocument"
          >
            Créer
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>
  </div>
</template>

<style scoped>
.cursor-pointer {
  cursor: pointer;
}
</style>
