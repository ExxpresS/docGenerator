<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import CardStatisticsHorizontal from '@core/components/cards/CardStatisticsHorizontal.vue'

definePage({
  meta: {
    layout: 'default',
  },
})

const apiStatus = ref(false)
const projectsCount = ref(0)
const workflowsCount = ref(0)
const documentsCount = ref(0)
const loading = ref(true)

const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'

onMounted(async () => {
  loading.value = true

  try {
    // Check API Status
    const healthResponse = await axios.get(`${apiUrl}/health`)
    if (healthResponse.data.status === 'ok') {
      apiStatus.value = true
    }

    // Fetch projects count
    const projectsResponse = await axios.get(`${apiUrl}/api/v1/projects/`)
    projectsCount.value = projectsResponse.data.length

    // Fetch workflows count for all projects
    let totalWorkflows = 0
    for (const project of projectsResponse.data) {
      try {
        const workflowsResponse = await axios.get(`${apiUrl}/api/v1/workflows/project/${project.id}`)
        totalWorkflows += workflowsResponse.data.length
      } catch (error) {
        console.error(`Error fetching workflows for project ${project.id}:`, error)
      }
    }
    workflowsCount.value = totalWorkflows

    // Fetch documents count
    const documentsResponse = await axios.get(`${apiUrl}/api/v1/documents/`)
    documentsCount.value = documentsResponse.data.length
  } catch (error) {
    console.error('API connection error:', error)
    apiStatus.value = false
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <!-- Welcome Card -->
    <VRow>
      <VCol cols="12">
        <VCard class="mb-6">
          <VCardText>
            <div class="d-flex align-center justify-space-between flex-wrap gap-4">
              <div>
                <h4 class="text-h4 mb-1">
                  Bienvenue sur Workflow Manager 🚀
                </h4>
                <p class="text-body-1 mb-0">
                  Capturez, documentez et interrogez vos workflows métier via RAG/LLM
                </p>
              </div>
              <div>
                <VChip
                  :color="apiStatus ? 'success' : 'error'"
                  :prepend-icon="apiStatus ? 'tabler-check' : 'tabler-x'"
                  variant="tonal"
                >
                  Backend API: {{ apiStatus ? 'Connecté' : 'Déconnecté' }}
                </VChip>
              </div>
            </div>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>

    <!-- Statistics Cards -->
    <VRow>
      <VCol
        cols="12"
        sm="6"
        md="4"
      >
        <CardStatisticsHorizontal
          title="Projets"
          :stats="loading ? '...' : String(projectsCount)"
          icon="tabler-folder"
          color="primary"
        />
      </VCol>

      <VCol
        cols="12"
        sm="6"
        md="4"
      >
        <CardStatisticsHorizontal
          title="Workflows"
          :stats="loading ? '...' : String(workflowsCount)"
          icon="tabler-sitemap"
          color="success"
        />
      </VCol>

      <VCol
        cols="12"
        sm="6"
        md="4"
      >
        <CardStatisticsHorizontal
          title="Documents"
          :stats="loading ? '...' : String(documentsCount)"
          icon="tabler-file-text"
          color="warning"
        />
      </VCol>
    </VRow>

    <!-- Quick Actions -->
    <VRow>
      <VCol cols="12">
        <VCard title="Actions rapides">
          <VCardText>
            <VRow>
              <VCol
                cols="12"
                sm="6"
                md="3"
              >
                <VCard
                  variant="tonal"
                  color="primary"
                  to="/projects"
                  :ripple="false"
                  class="cursor-pointer"
                >
                  <VCardText class="text-center pa-6">
                    <VAvatar
                      size="56"
                      color="primary"
                      variant="tonal"
                      class="mb-4"
                    >
                      <VIcon
                        icon="tabler-folder-plus"
                        size="32"
                      />
                    </VAvatar>
                    <h6 class="text-h6 mb-1">
                      Créer un projet
                    </h6>
                    <p class="text-sm mb-0">
                      Organisez vos workflows
                    </p>
                  </VCardText>
                </VCard>
              </VCol>

              <VCol
                cols="12"
                sm="6"
                md="3"
              >
                <VCard
                  variant="tonal"
                  color="success"
                  to="/workflows"
                  :ripple="false"
                  class="cursor-pointer"
                >
                  <VCardText class="text-center pa-6">
                    <VAvatar
                      size="56"
                      color="success"
                      variant="tonal"
                      class="mb-4"
                    >
                      <VIcon
                        icon="tabler-sitemap"
                        size="32"
                      />
                    </VAvatar>
                    <h6 class="text-h6 mb-1">
                      Voir les workflows
                    </h6>
                    <p class="text-sm mb-0">
                      Parcourez vos captures
                    </p>
                  </VCardText>
                </VCard>
              </VCol>

              <VCol
                cols="12"
                sm="6"
                md="3"
              >
                <VCard
                  variant="tonal"
                  color="warning"
                  to="/documents"
                  :ripple="false"
                  class="cursor-pointer"
                >
                  <VCardText class="text-center pa-6">
                    <VAvatar
                      size="56"
                      color="warning"
                      variant="tonal"
                      class="mb-4"
                    >
                      <VIcon
                        icon="tabler-file-text"
                        size="32"
                      />
                    </VAvatar>
                    <h6 class="text-h6 mb-1">
                      Documents
                    </h6>
                    <p class="text-sm mb-0">
                      Documentation auto
                    </p>
                  </VCardText>
                </VCard>
              </VCol>

              <VCol
                cols="12"
                sm="6"
                md="3"
              >
                <VCard
                  variant="tonal"
                  color="info"
                  href="chrome://extensions/"
                  target="_blank"
                  :ripple="false"
                  class="cursor-pointer"
                >
                  <VCardText class="text-center pa-6">
                    <VAvatar
                      size="56"
                      color="info"
                      variant="tonal"
                      class="mb-4"
                    >
                      <VIcon
                        icon="tabler-puzzle"
                        size="32"
                      />
                    </VAvatar>
                    <h6 class="text-h6 mb-1">
                      Extension
                    </h6>
                    <p class="text-sm mb-0">
                      Installer l'extension
                    </p>
                  </VCardText>
                </VCard>
              </VCol>
            </VRow>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>

    <!-- Getting Started -->
    <VRow>
      <VCol cols="12">
        <VCard>
          <VCardText>
            <div class="d-flex align-center gap-4 mb-4">
              <VAvatar
                color="primary"
                variant="tonal"
                size="48"
              >
                <VIcon
                  icon="tabler-rocket"
                  size="28"
                />
              </VAvatar>
              <div>
                <h5 class="text-h5 mb-0">
                  Démarrage rapide
                </h5>
                <p class="text-sm text-disabled mb-0">
                  Suivez ces étapes pour commencer
                </p>
              </div>
            </div>

            <VTimeline
              side="end"
              align="start"
              line-inset="8"
              truncate-line="start"
              density="compact"
            >
              <VTimelineItem
                dot-color="primary"
                size="x-small"
              >
                <div class="d-flex justify-space-between align-center flex-wrap mb-2">
                  <h6 class="text-h6 me-2">
                    Créer un projet
                  </h6>
                  <VChip
                    color="primary"
                    size="small"
                    variant="tonal"
                  >
                    Étape 1
                  </VChip>
                </div>
                <p class="text-sm mb-1">
                  Créez votre premier projet pour organiser vos workflows
                </p>
                <RouterLink
                  to="/projects"
                  class="text-sm"
                >
                  Aller aux projets →
                </RouterLink>
              </VTimelineItem>

              <VTimelineItem
                dot-color="success"
                size="x-small"
              >
                <div class="d-flex justify-space-between align-center flex-wrap mb-2">
                  <h6 class="text-h6 me-2">
                    Installer l'extension
                  </h6>
                  <VChip
                    color="success"
                    size="small"
                    variant="tonal"
                  >
                    Étape 2
                  </VChip>
                </div>
                <p class="text-sm mb-1">
                  Installez l'extension Chrome pour capturer vos workflows
                </p>
                <a
                  href="https://github.com/yourusername/workflow-manager/tree/main/extension"
                  target="_blank"
                  class="text-sm"
                >
                  Guide d'installation →
                </a>
              </VTimelineItem>

              <VTimelineItem
                dot-color="warning"
                size="x-small"
              >
                <div class="d-flex justify-space-between align-center flex-wrap mb-2">
                  <h6 class="text-h6 me-2">
                    Capturer un workflow
                  </h6>
                  <VChip
                    color="warning"
                    size="small"
                    variant="tonal"
                  >
                    Étape 3
                  </VChip>
                </div>
                <p class="text-sm mb-0">
                  Utilisez l'extension pour enregistrer vos parcours utilisateur
                </p>
              </VTimelineItem>

              <VTimelineItem
                dot-color="info"
                size="x-small"
              >
                <div class="d-flex justify-space-between align-center flex-wrap mb-2">
                  <h6 class="text-h6 me-2">
                    Générer la documentation
                  </h6>
                  <VChip
                    color="info"
                    size="small"
                    variant="tonal"
                  >
                    Étape 4
                  </VChip>
                </div>
                <p class="text-sm mb-0">
                  Créez automatiquement de la documentation depuis vos workflows
                </p>
              </VTimelineItem>
            </VTimeline>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>
  </div>
</template>

<style scoped>
.cursor-pointer {
  cursor: pointer;
  transition: transform 0.2s;
}

.cursor-pointer:hover {
  transform: translateY(-4px);
}
</style>
