<template>
  <div class="dashboard">
    <h2>Dashboard</h2>
    <p>Welcome to Workflow Manager</p>
    <div class="info">
      <p>Backend API Status: <span :class="apiStatus ? 'success' : 'error'">{{ apiStatus ? 'Connected' : 'Disconnected' }}</span></p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const apiStatus = ref(false)

onMounted(async () => {
  try {
    const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    const response = await axios.get(`${apiUrl}/health`)
    if (response.data.status === 'ok') {
      apiStatus.value = true
    }
  } catch (error) {
    console.error('API connection error:', error)
  }
})
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
  margin: 0 auto;
}

h2 {
  color: #2c3e50;
  margin-bottom: 1rem;
}

.info {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-top: 1rem;
}

.success {
  color: #28a745;
  font-weight: bold;
}

.error {
  color: #dc3545;
  font-weight: bold;
}
</style>
