<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

definePage({
  meta: {
    layout: 'default',
  },
})

const router = useRouter()

const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'

const projects = ref([])
const loading = ref(false)
const dialog = ref(false)
const deleteDialog = ref(false)
const editMode = ref(false)
const projectToDelete = ref(null)
const search = ref('')

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
  { title: 'Créé le', key: 'created_at', sortable: true },
  { title: 'Workflows', key: 'workflow_count', sortable: true },
  { title: 'Actions', key: 'actions', sortable: false, align: 'end' }
]

const fetchProjects = async () => {
  loading.value = true
  try {
    const response = await axios.get(`${apiUrl}/api/v1/projects/`)

    // Fetch stats for each project
    const projectsWithStats = await Promise.all(
      response.data.map(async (project) => {
        try {
          const statsResponse = await axios.get(`${apiUrl}/api/v1/projects/${project.id}/stats`)

return { ...project, workflow_count: statsResponse.data.workflow_count }
        } catch (error) {
          return { ...project, workflow_count: 0 }
        }
      })
    )

    projects.value = projectsWithStats
  } catch (error) {
    showSnackbar('Erreur lors du chargement des projets', 'error')
    console.error('Error fetching projects:', error)
  } finally {
    loading.value = false
  }
}

const openCreateDialog = () => {
  editMode.value = false
  formData.value = { name: '', description: '' }
  dialog.value = true
}

const openEditDialog = (project) => {
  editMode.value = true
  formData.value = {
    id: project.id,
    name: project.name,
    description: project.description
  }
  dialog.value = true
}

const saveProject = async () => {
  if (!formData.value.name) {
    showSnackbar('Le nom du projet est requis', 'error')

return
  }

  try {
    if (editMode.value) {
      await axios.put(`${apiUrl}/api/v1/projects/${formData.value.id}`, {
        name: formData.value.name,
        description: formData.value.description
      })
      showSnackbar('Projet modifié avec succès', 'success')
    } else {
      await axios.post(`${apiUrl}/api/v1/projects/`, {
        name: formData.value.name,
        description: formData.value.description
      })
      showSnackbar('Projet créé avec succès', 'success')
    }

    dialog.value = false
    await fetchProjects()
  } catch (error) {
    showSnackbar('Erreur lors de la sauvegarde du projet', 'error')
    console.error('Error saving project:', error)
  }
}

const confirmDelete = (project) => {
  projectToDelete.value = project
  deleteDialog.value = true
}

const deleteProject = async () => {
  try {
    await axios.delete(`${apiUrl}/api/v1/projects/${projectToDelete.value.id}`)
    showSnackbar('Projet supprimé avec succès', 'success')
    deleteDialog.value = false
    await fetchProjects()
  } catch (error) {
    showSnackbar('Erreur lors de la suppression du projet', 'error')
    console.error('Error deleting project:', error)
  }
}

const viewWorkflows = (projectId) => {
  router.push(`/workflows/${projectId}`)
}

const formatDate = (dateString) => {
  if (!dateString) return '-'

return new Date(dateString).toLocaleDateString('fr-FR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

const showSnackbar = (text, color = 'success') => {
  snackbarText.value = text
  snackbarColor.value = color
  snackbar.value = true
}

onMounted(() => {
  fetchProjects()
})
</script>

<template>
  <div>
    <!-- Header -->
    <div class="d-flex flex-wrap justify-space-between align-center gap-4 mb-6">
      <div>
        <h4 class="text-h4 mb-1">
          Projets
        </h4>
        <p class="text-body-1 mb-0">
          Organisez vos workflows par projet
        </p>
      </div>
      <VBtn
        prepend-icon="tabler-plus"
        @click="openCreateDialog"
      >
        Nouveau Projet
      </VBtn>
    </div>

    <!-- Projects Table Card -->
    <VCard>
      <VCardText class="d-flex align-center flex-wrap gap-4">
        <div class="me-3 d-flex gap-3">
          <VTextField
            v-model="search"
            prepend-inner-icon="tabler-search"
            placeholder="Rechercher un projet..."
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
            @click="fetchProjects"
          >
            <VIcon icon="tabler-refresh" />
          </VBtn>
        </div>
      </VCardText>

      <VDivider />

      <VDataTable
        :headers="headers"
        :items="projects"
        :search="search"
        :loading="loading"
        :items-per-page="10"
        class="text-no-wrap"
      >
        <template #item.created_at="{ item }">
          <span class="text-body-2">{{ formatDate(item.created_at) }}</span>
        </template>

        <template #item.workflow_count="{ item }">
          <VChip
            color="primary"
            variant="tonal"
            size="small"
          >
            {{ item.workflow_count || 0 }}
          </VChip>
        </template>

        <template #item.actions="{ item }">
          <div class="d-flex gap-1">
            <VBtn
              icon
              variant="text"
              color="primary"
              size="small"
              @click="viewWorkflows(item.id)"
            >
              <VIcon icon="tabler-sitemap" />
              <VTooltip
                activator="parent"
                location="top"
              >
                Workflows
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
              {{ projects.length }} projet(s) au total
            </p>
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
              {{ editMode ? 'Modifier le Projet' : 'Nouveau Projet' }}
            </h5>
            <p class="text-body-1">
              {{ editMode ? 'Mettez à jour les informations du projet' : 'Créez un nouveau projet pour organiser vos workflows' }}
            </p>
          </div>

          <VForm @submit.prevent="saveProject">
            <VRow>
              <VCol cols="12">
                <VTextField
                  v-model="formData.name"
                  label="Nom du projet"
                  placeholder="Mon projet"
                  :rules="[v => !!v || 'Le nom est requis']"
                  required
                />
              </VCol>

              <VCol cols="12">
                <VTextarea
                  v-model="formData.description"
                  label="Description"
                  placeholder="Description du projet..."
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
              Êtes-vous sûr de vouloir supprimer le projet <strong>"{{ projectToDelete?.name }}"</strong> ?
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
              @click="deleteProject"
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
