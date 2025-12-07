<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

definePage({
  meta: {
    layout: 'default',
  },
})

const route = useRoute()
const router = useRouter()
const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'

const projectId = computed(() => route.params.projectId)
const project = ref(null)
const workflows = ref([])
const loading = ref(false)
const detailsDialog = ref(false)
const editDialog = ref(false)
const deleteDialog = ref(false)
const selectedWorkflow = ref(null)
const workflowDetails = ref(null)
const workflowToDelete = ref(null)
const search = ref('')

const snackbar = ref(false)
const snackbarText = ref('')
const snackbarColor = ref('success')

const formData = ref({
  name: '',
  description: ''
})

const headers = [
  { title: 'ID', key: 'id', sortable: true, width: '80px' },
  { title: 'Nom', key: 'name', sortable: true },
  { title: 'URL', key: 'url', sortable: false },
  { title: 'Domaine', key: 'domain', sortable: true },
  { title: 'Durée', key: 'duration_ms', sortable: true },
  { title: 'Créé le', key: 'created_at', sortable: true },
  { title: 'Actions', key: 'actions', sortable: false, align: 'end', width: '120px' }
]

const fetchProject = async () => {
  try {
    const response = await axios.get(`${apiUrl}/api/v1/projects/${projectId.value}`)
    project.value = response.data
  } catch (error) {
    showSnackbar('Erreur lors du chargement du projet', 'error')
    console.error('Error fetching project:', error)
  }
}

const fetchWorkflows = async () => {
  loading.value = true
  try {
    const response = await axios.get(`${apiUrl}/api/v1/workflows/project/${projectId.value}`)
    workflows.value = response.data
  } catch (error) {
    showSnackbar('Erreur lors du chargement des workflows', 'error')
    console.error('Error fetching workflows:', error)
  } finally {
    loading.value = false
  }
}

const viewWorkflowDetails = async (workflow) => {
  try {
    const response = await axios.get(`${apiUrl}/api/v1/workflows/${workflow.id}?include_details=true`)
    workflowDetails.value = response.data
    selectedWorkflow.value = workflow
    detailsDialog.value = true
  } catch (error) {
    showSnackbar('Erreur lors du chargement des détails', 'error')
    console.error('Error fetching workflow details:', error)
  }
}

const openEditDialog = (workflow) => {
  formData.value = {
    id: workflow.id,
    name: workflow.name,
    description: workflow.description
  }
  editDialog.value = true
}

const saveWorkflow = async () => {
  if (!formData.value.name) {
    showSnackbar('Le nom du workflow est requis', 'error')
    return
  }

  try {
    await axios.put(`${apiUrl}/api/v1/workflows/${formData.value.id}`, {
      name: formData.value.name,
      description: formData.value.description
    })
    showSnackbar('Workflow modifié avec succès', 'success')
    editDialog.value = false
    await fetchWorkflows()
  } catch (error) {
    showSnackbar('Erreur lors de la modification du workflow', 'error')
    console.error('Error saving workflow:', error)
  }
}

const confirmDelete = (workflow) => {
  workflowToDelete.value = workflow
  deleteDialog.value = true
}

const deleteWorkflow = async () => {
  try {
    await axios.delete(`${apiUrl}/api/v1/workflows/${workflowToDelete.value.id}`)
    showSnackbar('Workflow supprimé avec succès', 'success')
    deleteDialog.value = false
    await fetchWorkflows()
  } catch (error) {
    showSnackbar('Erreur lors de la suppression du workflow', 'error')
    console.error('Error deleting workflow:', error)
  }
}

const goBackToProjects = () => {
  router.push({ name: 'projects' })
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

const formatDuration = (ms) => {
  if (!ms) return '-'
  const seconds = Math.floor(ms / 1000)
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return minutes > 0 ? `${minutes}m ${remainingSeconds}s` : `${seconds}s`
}

const truncateUrl = (url) => {
  if (!url) return '-'
  return url.length > 40 ? url.substring(0, 40) + '...' : url
}

const getStateIcon = (stateType) => {
  const icons = {
    'page_view': 'tabler-eye',
    'page_unload': 'tabler-logout',
    'default': 'tabler-circle-dot'
  }
  return icons[stateType] || icons.default
}

const getActionIcon = (actionType) => {
  const icons = {
    'click': 'tabler-pointer',
    'input': 'tabler-keyboard',
    'submit': 'tabler-send',
    'default': 'tabler-click'
  }
  return icons[actionType] || icons.default
}

const showSnackbar = (text, color = 'success') => {
  snackbarText.value = text
  snackbarColor.value = color
  snackbar.value = true
}

onMounted(async () => {
  await fetchProject()
  await fetchWorkflows()
})
</script>

<template>
  <div>
    <!-- Header -->
    <div class="d-flex flex-wrap justify-space-between align-center gap-4 mb-6">
      <div>
        <div class="d-flex align-center gap-2 mb-1">
          <VBtn
            icon
            variant="text"
            color="default"
            size="small"
            @click="goBackToProjects"
          >
            <VIcon icon="tabler-arrow-left" />
          </VBtn>
          <h4 class="text-h4 mb-0">
            Workflows - {{ project?.name || 'Chargement...' }}
          </h4>
        </div>
        <p class="text-body-1 mb-0 ms-12">
          Gérez les parcours utilisateurs de ce projet
        </p>
      </div>
    </div>

    <!-- Workflows Table Card -->
    <VCard>
      <VCardText class="d-flex align-center flex-wrap gap-4">
        <div class="me-3 d-flex gap-3">
          <VTextField
            v-model="search"
            prepend-inner-icon="tabler-search"
            placeholder="Rechercher un workflow..."
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
            @click="fetchWorkflows"
          >
            <VIcon icon="tabler-refresh" />
          </VBtn>
        </div>
      </VCardText>

      <VDivider />

      <VDataTable
        :headers="headers"
        :items="workflows"
        :search="search"
        :loading="loading"
        :items-per-page="10"
        class="text-no-wrap"
      >
        <template #item.url="{ item }">
          <a
            :href="item.url"
            target="_blank"
            class="text-primary text-decoration-none"
          >
            {{ truncateUrl(item.url) }}
            <VIcon
              icon="tabler-external-link"
              size="14"
              class="ms-1"
            />
          </a>
        </template>

        <template #item.duration_ms="{ item }">
          <VChip
            color="info"
            variant="tonal"
            size="small"
          >
            {{ formatDuration(item.duration_ms) }}
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
              color="default"
              size="small"
              @click="viewWorkflowDetails(item)"
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

        <template #bottom>
          <VDivider />
          <div class="d-flex align-center justify-space-between flex-wrap gap-3 pa-5 pb-3">
            <p class="text-sm text-disabled mb-0">
              {{ workflows.length }} workflow(s) au total
            </p>
          </div>
        </template>
      </VDataTable>
    </VCard>

    <!-- Details Dialog -->
    <VDialog
      v-model="detailsDialog"
      max-width="900"
      scrollable
    >
      <VCard v-if="selectedWorkflow">
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
              {{ selectedWorkflow.name }}
            </h5>
            <div class="d-flex gap-2 flex-wrap">
              <VChip
                color="primary"
                size="small"
                prepend-icon="tabler-link"
              >
                {{ selectedWorkflow.domain }}
              </VChip>
              <VChip
                color="info"
                size="small"
                prepend-icon="tabler-clock"
              >
                {{ formatDuration(selectedWorkflow.duration_ms) }}
              </VChip>
            </div>
          </div>

          <VRow>
            <VCol cols="12">
              <h6 class="text-h6 mb-3">
                Informations
              </h6>
              <VList>
                <VListItem>
                  <template #prepend>
                    <VIcon
                      icon="tabler-world"
                      class="me-2"
                    />
                  </template>
                  <VListItemTitle class="text-sm font-weight-medium">
                    URL
                  </VListItemTitle>
                  <VListItemSubtitle>
                    <a
                      :href="selectedWorkflow.url"
                      target="_blank"
                      class="text-primary"
                    >
                      {{ selectedWorkflow.url }}
                    </a>
                  </VListItemSubtitle>
                </VListItem>

                <VListItem>
                  <template #prepend>
                    <VIcon
                      icon="tabler-hash"
                      class="me-2"
                    />
                  </template>
                  <VListItemTitle class="text-sm font-weight-medium">
                    Hash
                  </VListItemTitle>
                  <VListItemSubtitle>
                    <code class="text-caption">{{ selectedWorkflow.workflow_hash }}</code>
                  </VListItemSubtitle>
                </VListItem>
              </VList>
            </VCol>

            <VCol
              v-if="workflowDetails?.states?.length"
              cols="12"
            >
              <h6 class="text-h6 mb-3">
                États ({{ workflowDetails.states.length }})
              </h6>
              <VExpansionPanels>
                <VExpansionPanel
                  v-for="(state, index) in workflowDetails.states"
                  :key="index"
                >
                  <VExpansionPanelTitle>
                    <div class="d-flex align-center gap-2">
                      <VIcon
                        :icon="getStateIcon(state.state_type)"
                        size="20"
                      />
                      <span class="font-weight-medium">{{ state.state_type }}</span>
                      <VChip
                        size="x-small"
                        variant="tonal"
                      >
                        {{ state.url || 'N/A' }}
                      </VChip>
                    </div>
                  </VExpansionPanelTitle>
                  <VExpansionPanelText>
                    <pre class="text-caption pa-2 bg-surface-variant rounded">{{ JSON.stringify(state.data, null, 2) }}</pre>
                  </VExpansionPanelText>
                </VExpansionPanel>
              </VExpansionPanels>
            </VCol>

            <VCol
              v-if="workflowDetails?.actions?.length"
              cols="12"
            >
              <h6 class="text-h6 mb-3">
                Actions ({{ workflowDetails.actions.length }})
              </h6>
              <VExpansionPanels>
                <VExpansionPanel
                  v-for="(action, index) in workflowDetails.actions"
                  :key="index"
                >
                  <VExpansionPanelTitle>
                    <div class="d-flex align-center gap-2">
                      <VIcon
                        :icon="getActionIcon(action.action_type)"
                        size="20"
                      />
                      <span class="font-weight-medium">{{ action.action_type }}</span>
                      <VChip
                        size="x-small"
                        variant="tonal"
                      >
                        {{ action.element_tag || 'N/A' }}
                      </VChip>
                    </div>
                  </VExpansionPanelTitle>
                  <VExpansionPanelText>
                    <pre class="text-caption pa-2 bg-surface-variant rounded">{{ JSON.stringify(action.data, null, 2) }}</pre>
                  </VExpansionPanelText>
                </VExpansionPanel>
              </VExpansionPanels>
            </VCol>
          </VRow>
        </VCardText>
      </VCard>
    </VDialog>

    <!-- Edit Dialog -->
    <VDialog
      v-model="editDialog"
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
            @click="editDialog = false"
          >
            <VIcon
              size="20"
              icon="tabler-x"
            />
          </VBtn>

          <div class="text-center mb-6">
            <h5 class="text-h5 mb-2">
              Modifier le Workflow
            </h5>
            <p class="text-body-1">
              Mettez à jour les informations du workflow
            </p>
          </div>

          <VForm @submit.prevent="saveWorkflow">
            <VRow>
              <VCol cols="12">
                <VTextField
                  v-model="formData.name"
                  label="Nom du workflow"
                  placeholder="Mon workflow"
                  :rules="[v => !!v || 'Le nom est requis']"
                  required
                />
              </VCol>

              <VCol cols="12">
                <VTextarea
                  v-model="formData.description"
                  label="Description"
                  placeholder="Description du workflow..."
                  rows="3"
                />
              </VCol>

              <VCol
                cols="12"
                class="d-flex gap-4"
              >
                <VBtn
                  color="secondary"
                  variant="tonal"
                  @click="editDialog = false"
                >
                  Annuler
                </VBtn>
                <VSpacer />
                <VBtn
                  type="submit"
                  @click="saveWorkflow"
                >
                  Modifier
                </VBtn>
              </VCol>
            </VRow>
          </VForm>
        </VCardText>
      </VCard>
    </VDialog>

    <!-- Delete Confirmation Dialog -->
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
              Êtes-vous sûr de vouloir supprimer le workflow <strong>"{{ workflowToDelete?.name }}"</strong> ?
            </p>
          </div>

          <div class="d-flex gap-4">
            <VBtn
              color="secondary"
              variant="tonal"
              block
              @click="deleteDialog = false"
            >
              Annuler
            </VBtn>
            <VBtn
              color="error"
              block
              @click="deleteWorkflow"
            >
              Supprimer
            </VBtn>
          </div>
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
