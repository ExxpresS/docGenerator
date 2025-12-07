/**
 * Popup Script for Workflow Capture Extension
 * Handles UI interactions and communication with background script
 */

// UI Elements
const elements = {
  statusIndicator: document.getElementById('statusIndicator'),
  statusText: document.getElementById('statusText'),
  recordingInfo: document.getElementById('recordingInfo'),
  workflowName: document.getElementById('workflowName'),
  actionsCount: document.getElementById('actionsCount'),
  statesCount: document.getElementById('statesCount'),
  duration: document.getElementById('duration'),

  startForm: document.getElementById('startForm'),
  stopForm: document.getElementById('stopForm'),
  workflowNameInput: document.getElementById('workflowNameInput'),
  projectIdInput: document.getElementById('projectIdInput'),
  startBtn: document.getElementById('startBtn'),
  stopBtn: document.getElementById('stopBtn'),

  workflowPreview: document.getElementById('workflowPreview'),
  workflowJson: document.getElementById('workflowJson'),
  syncBtn: document.getElementById('syncBtn'),
  cancelBtn: document.getElementById('cancelBtn'),

  syncResult: document.getElementById('syncResult'),
  syncAlert: document.getElementById('syncAlert'),

  settingsToggle: document.getElementById('settingsToggle'),
  settingsPanel: document.getElementById('settingsPanel'),
  apiUrlInput: document.getElementById('apiUrlInput'),
  saveSettingsBtn: document.getElementById('saveSettingsBtn')
};

// State
let currentWorkflow = null;
let durationInterval = null;

/**
 * Initialize popup
 */
async function init() {
  // Load settings
  const { apiUrl = 'http://localhost:8001/api/v1', projectId = 1 } = await chrome.storage.sync.get(['apiUrl', 'projectId']);
  elements.apiUrlInput.value = apiUrl;
  elements.projectIdInput.value = projectId;

  // Check recording status
  await updateStatus();

  // Set up event listeners
  setupEventListeners();
}

/**
 * Update UI based on recording status
 */
async function updateStatus() {
  try {
    const response = await chrome.runtime.sendMessage({ type: 'GET_RECORDING_STATUS' });

    if (response.isRecording) {
      showRecordingState(response.currentWorkflow);
    } else {
      showIdleState();
    }
  } catch (error) {
    console.error('Failed to get recording status:', error);
  }
}

/**
 * Show idle state
 */
function showIdleState() {
  elements.statusText.textContent = 'Ready';
  elements.statusIndicator.querySelector('.dot').classList.remove('recording');
  elements.recordingInfo.classList.add('hidden');
  elements.startForm.classList.remove('hidden');
  elements.stopForm.classList.add('hidden');
  elements.workflowPreview.classList.add('hidden');

  if (durationInterval) {
    clearInterval(durationInterval);
    durationInterval = null;
  }
}

/**
 * Show recording state
 */
function showRecordingState(workflow) {
  elements.statusText.textContent = 'Recording...';
  elements.statusIndicator.querySelector('.dot').classList.add('recording');
  elements.recordingInfo.classList.remove('hidden');
  elements.startForm.classList.add('hidden');
  elements.stopForm.classList.remove('hidden');
  elements.workflowPreview.classList.add('hidden');

  if (workflow) {
    elements.workflowName.textContent = workflow.name;
    elements.actionsCount.textContent = workflow.actionsCount || 0;
    elements.statesCount.textContent = workflow.statesCount || 0;

    // Update duration every second
    if (!durationInterval) {
      durationInterval = setInterval(() => {
        const seconds = Math.floor((workflow.duration || 0) / 1000);
        elements.duration.textContent = `${seconds}s`;
      }, 1000);
    }
  }
}

/**
 * Show workflow preview
 */
function showWorkflowPreview(workflow) {
  currentWorkflow = workflow;

  elements.statusText.textContent = 'Workflow Captured';
  elements.statusIndicator.querySelector('.dot').classList.remove('recording');
  elements.recordingInfo.classList.add('hidden');
  elements.startForm.classList.add('hidden');
  elements.stopForm.classList.add('hidden');
  elements.workflowPreview.classList.remove('hidden');

  // Display workflow JSON (simplified)
  const preview = {
    name: workflow.name,
    url: workflow.url,
    domain: workflow.domain,
    duration_ms: workflow.duration_ms,
    actions_count: workflow.actions.length,
    states_count: workflow.states.length,
    hash: workflow.workflow_hash
  };

  elements.workflowJson.textContent = JSON.stringify(preview, null, 2);
}

/**
 * Show sync result
 */
function showSyncResult(success, message) {
  elements.syncResult.classList.remove('hidden');

  if (success) {
    elements.syncAlert.className = 'alert success';
    elements.syncAlert.textContent = `✅ ${message}`;
  } else {
    elements.syncAlert.className = 'alert error';
    elements.syncAlert.textContent = `❌ ${message}`;
  }

  // Hide after 3 seconds
  setTimeout(() => {
    elements.syncResult.classList.add('hidden');
  }, 3000);
}

/**
 * Set up event listeners
 */
function setupEventListeners() {
  // Start recording
  elements.startBtn.addEventListener('click', async () => {
    const workflowName = elements.workflowNameInput.value.trim();
    const projectId = parseInt(elements.projectIdInput.value);

    if (!workflowName) {
      alert('Please enter a workflow name');
      return;
    }

    try {
      await chrome.runtime.sendMessage({
        type: 'START_RECORDING',
        data: { workflowName, projectId }
      });

      // Save project ID for next time
      await chrome.storage.sync.set({ projectId });

      await updateStatus();
    } catch (error) {
      console.error('Failed to start recording:', error);
      alert('Failed to start recording');
    }
  });

  // Stop recording
  elements.stopBtn.addEventListener('click', async () => {
    try {
      const response = await chrome.runtime.sendMessage({ type: 'STOP_RECORDING' });

      if (response.workflow) {
        showWorkflowPreview(response.workflow);
      } else {
        showIdleState();
      }
    } catch (error) {
      console.error('Failed to stop recording:', error);
      alert('Failed to stop recording');
    }
  });

  // Sync workflow
  elements.syncBtn.addEventListener('click', async () => {
    if (!currentWorkflow) return;

    try {
      elements.syncBtn.disabled = true;
      elements.syncBtn.innerHTML = '<span>⏳ Syncing...</span>';

      const response = await chrome.runtime.sendMessage({
        type: 'SYNC_WORKFLOW',
        data: { workflow: currentWorkflow }
      });

      if (response.success) {
        showSyncResult(true, 'Workflow synced successfully!');
        setTimeout(() => {
          currentWorkflow = null;
          showIdleState();
        }, 1500);
      } else {
        if (response.error === 'duplicate') {
          showSyncResult(false, 'Workflow already exists (duplicate detected)');
        } else {
          showSyncResult(false, `Sync failed: ${response.message}`);
        }
        elements.syncBtn.disabled = false;
        elements.syncBtn.innerHTML = '<span>🔄 Sync to Server</span>';
      }
    } catch (error) {
      console.error('Failed to sync workflow:', error);
      showSyncResult(false, `Sync failed: ${error.message}`);
      elements.syncBtn.disabled = false;
      elements.syncBtn.innerHTML = '<span>🔄 Sync to Server</span>';
    }
  });

  // Cancel workflow
  elements.cancelBtn.addEventListener('click', () => {
    currentWorkflow = null;
    showIdleState();
  });

  // Toggle settings
  elements.settingsToggle.addEventListener('click', () => {
    elements.settingsPanel.classList.toggle('hidden');
  });

  // Save settings
  elements.saveSettingsBtn.addEventListener('click', async () => {
    const apiUrl = elements.apiUrlInput.value.trim();

    if (!apiUrl) {
      alert('Please enter an API URL');
      return;
    }

    try {
      await chrome.storage.sync.set({ apiUrl });
      alert('Settings saved!');
      elements.settingsPanel.classList.add('hidden');
    } catch (error) {
      console.error('Failed to save settings:', error);
      alert('Failed to save settings');
    }
  });

  // Enter key on workflow name input
  elements.workflowNameInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      elements.startBtn.click();
    }
  });
}

// Initialize on load
document.addEventListener('DOMContentLoaded', init);
