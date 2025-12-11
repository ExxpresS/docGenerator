<script setup>
import { ref, nextTick, computed, onMounted } from 'vue'
import axios from 'axios'

definePage({
  meta: {
    layout: 'default',
  },
})

// API Configuration
const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'

// Chat State
const messages = ref([])
const userMessage = ref('')
const isLoading = ref(false)
const error = ref(null)
const chatContainer = ref(null)

// RAG State
const rags = ref([])
const selectedRagId = ref(null)
const isLoadingRags = ref(false)

// Computed property to check if message is empty
const canSend = computed(() => {
  return userMessage.value.trim().length > 0 && !isLoading.value
})

// Format timestamp
const formatTime = (isoString) => {
  const date = new Date(isoString)
  return date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
}

// Scroll to bottom of chat
const scrollToBottom = async () => {
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

// Load available RAGs
const loadRags = async () => {
  isLoadingRags.value = true
  try {
    const response = await axios.get(`${apiUrl}/api/v1/rags/`)
    rags.value = response.data
  } catch (err) {
    console.error('Error loading RAGs:', err)
  } finally {
    isLoadingRags.value = false
  }
}

// Load RAGs on mount
onMounted(() => {
  loadRags()
})

// Send message to LLM
const sendMessage = async () => {
  if (!canSend.value) return

  const messageText = userMessage.value.trim()
  error.value = null

  // Add user message to chat
  const userMsg = {
    role: 'user',
    content: messageText,
    timestamp: new Date().toISOString()
  }
  messages.value.push(userMsg)

  // Clear input
  userMessage.value = ''

  // Scroll to bottom
  await scrollToBottom()

  // Set loading state
  isLoading.value = true

  try {
    // Call backend API with optional rag_id
    const payload = { message: messageText }
    if (selectedRagId.value) {
      payload.rag_id = selectedRagId.value
    }
    const response = await axios.post(`${apiUrl}/api/v1/chat/`, payload)

    // Add assistant response to chat with RAG metadata
    const assistantMsg = {
      role: 'assistant',
      content: response.data.response,
      timestamp: response.data.timestamp,
      duration_ms: response.data.duration_ms,
      model: response.data.model,
      rag_used: response.data.rag_used,
      documents_used: response.data.documents_used,
      retrieval_time_ms: response.data.retrieval_time_ms
    }
    messages.value.push(assistantMsg)

    // Scroll to bottom
    await scrollToBottom()
  } catch (err) {
    console.error('Error sending message:', err)

    // Add error message to chat
    const errorMsg = {
      role: 'error',
      content: err.response?.data?.detail || 'Une erreur est survenue lors de la communication avec le LLM. Vérifiez que LM Studio est actif.',
      timestamp: new Date().toISOString()
    }
    messages.value.push(errorMsg)

    error.value = errorMsg.content
    await scrollToBottom()
  } finally {
    isLoading.value = false
  }
}

// Handle Enter key
const handleKeyDown = (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}

// Clear chat
const clearChat = () => {
  messages.value = []
  error.value = null
}
</script>

<template>
  <div class="chat-container">
    <!-- Header -->
    <VRow>
      <VCol cols="12">
        <VCard class="mb-4">
          <VCardText>
            <div class="d-flex align-center justify-space-between flex-wrap gap-4">
              <div class="d-flex align-center gap-3">
                <VAvatar
                  color="primary"
                  variant="tonal"
                  size="48"
                >
                  <VIcon
                    icon="tabler-message-chatbot"
                    size="28"
                  />
                </VAvatar>
                <div>
                  <h4 class="text-h4 mb-1">
                    Chat IA
                  </h4>
                  <p class="text-body-2 mb-0 text-disabled">
                    Discutez avec le modèle LLM via LM Studio
                  </p>
                </div>
              </div>
              <VBtn
                v-if="messages.length > 0"
                color="error"
                variant="tonal"
                prepend-icon="tabler-trash"
                @click="clearChat"
              >
                Effacer
              </VBtn>
            </div>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>

    <!-- RAG Selection -->
    <VRow v-if="rags.length > 0">
      <VCol cols="12">
        <VCard class="mb-4">
          <VCardText>
            <div class="d-flex align-center gap-3">
              <VIcon icon="tabler-database" size="24" />
              <VSelect
                v-model="selectedRagId"
                :items="rags"
                item-value="id"
                item-title="name"
                label="Base de connaissances (optionnel)"
                placeholder="Aucune base sélectionnée"
                clearable
                hide-details
                density="compact"
                variant="outlined"
                :loading="isLoadingRags"
              >
                <template #item="{ props, item }">
                  <VListItem v-bind="props">
                    <template #subtitle>
                      {{ item.raw.description || 'Aucune description' }}
                    </template>
                  </VListItem>
                </template>
              </VSelect>
              <VChip
                v-if="selectedRagId"
                color="success"
                variant="tonal"
                size="small"
              >
                RAG actif
              </VChip>
            </div>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>

    <!-- Chat Area -->
    <VRow>
      <VCol cols="12">
        <VCard
          class="chat-card"
          elevation="2"
        >
          <!-- Messages Container -->
          <VCardText
            ref="chatContainer"
            class="chat-messages"
          >
            <!-- Welcome Message -->
            <div
              v-if="messages.length === 0"
              class="welcome-message text-center"
            >
              <VAvatar
                color="primary"
                variant="tonal"
                size="80"
                class="mb-4"
              >
                <VIcon
                  icon="tabler-robot"
                  size="48"
                />
              </VAvatar>
              <h5 class="text-h5 mb-2">
                Bienvenue dans le Chat IA
              </h5>
              <p class="text-body-1 text-disabled mb-6">
                Posez vos questions et interagissez avec le modèle LLM
              </p>
              <div class="suggestion-chips">
                <VChip
                  class="ma-1"
                  variant="tonal"
                  @click="userMessage = 'Explique-moi ce qu\'est le RAG'"
                >
                  Qu'est-ce que le RAG ?
                </VChip>
                <VChip
                  class="ma-1"
                  variant="tonal"
                  @click="userMessage = 'Comment fonctionne un workflow ?'"
                >
                  Comment fonctionne un workflow ?
                </VChip>
                <VChip
                  class="ma-1"
                  variant="tonal"
                  @click="userMessage = 'Aide-moi à documenter mon code'"
                >
                  Aide pour la documentation
                </VChip>
              </div>
            </div>

            <!-- Messages -->
            <div
              v-for="(message, index) in messages"
              :key="index"
              class="message-wrapper"
              :class="message.role"
            >
              <div class="message-bubble">
                <!-- User Message -->
                <div
                  v-if="message.role === 'user'"
                  class="d-flex gap-3"
                >
                  <div class="message-content user-message">
                    <div class="message-text">
                      {{ message.content }}
                    </div>
                    <div class="message-time">
                      {{ formatTime(message.timestamp) }}
                    </div>
                  </div>
                  <VAvatar
                    color="primary"
                    size="40"
                  >
                    <VIcon icon="tabler-user" />
                  </VAvatar>
                </div>

                <!-- Assistant Message -->
                <div
                  v-else-if="message.role === 'assistant'"
                  class="d-flex gap-3"
                >
                  <VAvatar
                    color="success"
                    variant="tonal"
                    size="40"
                  >
                    <VIcon icon="tabler-robot" />
                  </VAvatar>
                  <div class="message-content assistant-message">
                    <div class="message-text">
                      {{ message.content }}
                    </div>
                    <div class="message-meta">
                      <span class="message-time">{{ formatTime(message.timestamp) }}</span>
                      <VChip
                        v-if="message.duration_ms"
                        size="x-small"
                        variant="text"
                        class="ml-2"
                      >
                        {{ Math.round(message.duration_ms) }}ms
                      </VChip>
                    </div>

                    <!-- Sources utilisées (RAG) -->
                    <div v-if="message.documents_used && message.documents_used.length > 0" class="mt-3">
                      <VDivider class="my-2" />
                      <div class="text-caption text-disabled mb-2">
                        Sources utilisées:
                      </div>
                      <div class="sources-list">
                        <VChip
                          v-for="(doc, idx) in message.documents_used"
                          :key="idx"
                          size="small"
                          variant="tonal"
                          color="primary"
                          class="ma-1"
                        >
                          {{ doc.title }}
                          <VTooltip activator="parent" location="top">
                            Score: {{ (doc.score * 100).toFixed(0) }}%
                          </VTooltip>
                        </VChip>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Error Message -->
                <div
                  v-else-if="message.role === 'error'"
                  class="d-flex gap-3"
                >
                  <VAvatar
                    color="error"
                    variant="tonal"
                    size="40"
                  >
                    <VIcon icon="tabler-alert-circle" />
                  </VAvatar>
                  <div class="message-content error-message">
                    <div class="message-text">
                      {{ message.content }}
                    </div>
                    <div class="message-time">
                      {{ formatTime(message.timestamp) }}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Loading Indicator -->
            <div
              v-if="isLoading"
              class="message-wrapper assistant"
            >
              <div class="message-bubble">
                <div class="d-flex gap-3">
                  <VAvatar
                    color="success"
                    variant="tonal"
                    size="40"
                  >
                    <VIcon icon="tabler-robot" />
                  </VAvatar>
                  <div class="message-content assistant-message">
                    <div class="typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </VCardText>

          <VDivider />

          <!-- Input Area -->
          <VCardText class="chat-input-area">
            <div class="d-flex gap-3 align-center">
              <VTextarea
                v-model="userMessage"
                placeholder="Tapez votre message..."
                rows="1"
                auto-grow
                variant="outlined"
                hide-details
                :disabled="isLoading"
                @keydown="handleKeyDown"
              />
              <VBtn
                icon
                color="primary"
                size="large"
                :disabled="!canSend"
                :loading="isLoading"
                @click="sendMessage"
              >
                <VIcon icon="tabler-send" />
              </VBtn>
            </div>
            <div class="text-caption text-disabled mt-2">
              Appuyez sur Entrée pour envoyer, Shift+Entrée pour un saut de ligne
            </div>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>
  </div>
</template>

<style scoped>
.chat-container {
  max-width: 1200px;
  margin: 0 auto;
}

.chat-card {
  height: calc(100vh - 280px);
  display: flex;
  flex-direction: column;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
  background: linear-gradient(to bottom, rgb(var(--v-theme-surface)), rgb(var(--v-theme-background)));
}

.welcome-message {
  padding: 3rem 1rem;
}

.suggestion-chips {
  max-width: 600px;
  margin: 0 auto;
}

.message-wrapper {
  margin-bottom: 1.5rem;
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-bubble {
  display: flex;
  flex-direction: column;
}

.message-wrapper.user .message-bubble {
  align-items: flex-end;
}

.message-wrapper.assistant .message-bubble,
.message-wrapper.error .message-bubble {
  align-items: flex-start;
}

.message-content {
  max-width: 70%;
  padding: 1rem 1.25rem;
  border-radius: 12px;
  word-wrap: break-word;
}

.user-message {
  background: rgb(var(--v-theme-primary));
  color: white;
  border-bottom-right-radius: 4px;
}

.assistant-message {
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-bottom-left-radius: 4px;
}

.error-message {
  background: rgba(var(--v-theme-error), 0.1);
  border: 1px solid rgba(var(--v-theme-error), 0.3);
  border-bottom-left-radius: 4px;
}

.message-text {
  white-space: pre-wrap;
  line-height: 1.6;
}

.message-time {
  font-size: 0.75rem;
  opacity: 0.7;
  margin-top: 0.5rem;
}

.message-meta {
  display: flex;
  align-items: center;
  margin-top: 0.5rem;
}

.chat-input-area {
  padding: 1.25rem;
  background: rgb(var(--v-theme-surface));
}

/* Typing indicator animation */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 8px 0;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgb(var(--v-theme-primary));
  opacity: 0.4;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    opacity: 0.4;
    transform: translateY(0);
  }
  30% {
    opacity: 1;
    transform: translateY(-10px);
  }
}

/* Scrollbar styling */
.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: transparent;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: rgba(var(--v-border-color), 0.3);
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: rgba(var(--v-border-color), 0.5);
}
</style>
