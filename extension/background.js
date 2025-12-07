/**
 * Background Service Worker for Workflow Capture
 * Manages workflow recording, state tracking, and API synchronization
 */

// Workflow recording state
let isRecording = false;
let currentWorkflow = null;
let recordingStartTime = null;

// Default API configuration
const DEFAULT_API_URL = 'http://localhost:8001/api/v1';
const DEFAULT_PROJECT_ID = 1;

/**
 * Initialize workflow recording
 */
function startRecording(workflowName, projectId) {
  isRecording = true;
  recordingStartTime = Date.now();

  currentWorkflow = {
    name: workflowName || 'Captured Workflow',
    project_id: projectId || DEFAULT_PROJECT_ID,
    description: `Captured on ${new Date().toISOString()}`,
    url: '',
    domain: '',
    duration_ms: 0,
    raw_data: {
      captured_at: new Date().toISOString(),
      user_agent: navigator.userAgent
    },
    workflow_hash: '',
    states: [],
    actions: []
  };

  // Get current tab info
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs[0]) {
      currentWorkflow.url = tabs[0].url;
      currentWorkflow.domain = new URL(tabs[0].url).hostname;
    }
  });

  // Notify content script to start capturing
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    chrome.tabs.sendMessage(tabs[0].id, {
      type: 'START_RECORDING',
      data: { workflowName }
    });
  });

  console.log('🎬 Recording started:', workflowName);
}

/**
 * Stop workflow recording
 */
function stopRecording() {
  if (!isRecording || !currentWorkflow) {
    return null;
  }

  isRecording = false;

  // Calculate duration
  currentWorkflow.duration_ms = Date.now() - recordingStartTime;

  // Generate workflow hash
  currentWorkflow.workflow_hash = generateWorkflowHash(currentWorkflow);

  // Notify content script to stop capturing
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    chrome.tabs.sendMessage(tabs[0].id, {
      type: 'STOP_RECORDING'
    });
  });

  console.log('⏹️ Recording stopped:', currentWorkflow);

  const workflow = { ...currentWorkflow };
  currentWorkflow = null;
  recordingStartTime = null;

  return workflow;
}

/**
 * Add action to current workflow
 */
function addAction(actionData) {
  if (!isRecording || !currentWorkflow) {
    return;
  }

  const action = {
    action_type: actionData.type,
    action_data: actionData.data,
    sequence_order: currentWorkflow.actions.length,
    timestamp: new Date().toISOString()
  };

  currentWorkflow.actions.push(action);
  console.log('➕ Action added:', action);
}

/**
 * Add state to current workflow
 */
function addState(stateData) {
  if (!isRecording || !currentWorkflow) {
    return;
  }

  const state = {
    state_type: stateData.type,
    state_data: stateData.data,
    sequence_order: currentWorkflow.states.length,
    timestamp: new Date().toISOString()
  };

  currentWorkflow.states.push(state);
  console.log('📊 State added:', state);
}

/**
 * Generate workflow hash for duplicate detection
 */
function generateWorkflowHash(workflow) {
  const hashData = JSON.stringify({
    url: workflow.url,
    domain: workflow.domain,
    actions: workflow.actions.map(a => a.action_type),
    states: workflow.states.map(s => s.state_type)
  });

  // Simple hash function (in production, use crypto.subtle.digest)
  let hash = 0;
  for (let i = 0; i < hashData.length; i++) {
    const char = hashData.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash;
  }

  return Math.abs(hash).toString(16);
}

/**
 * Sync workflow to backend API
 */
async function syncWorkflow(workflow) {
  try {
    // Get API URL from storage
    const { apiUrl = DEFAULT_API_URL } = await chrome.storage.sync.get('apiUrl');

    const response = await fetch(`${apiUrl}/workflows/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(workflow)
    });

    if (!response.ok) {
      const error = await response.json();

      // Handle duplicate workflow
      if (response.status === 409) {
        console.warn('⚠️ Workflow already exists (duplicate hash)');
        return { success: false, error: 'duplicate', message: error.detail };
      }

      throw new Error(error.detail || 'Failed to sync workflow');
    }

    const result = await response.json();
    console.log('✅ Workflow synced successfully:', result);

    return { success: true, data: result };
  } catch (error) {
    console.error('❌ Failed to sync workflow:', error);
    return { success: false, error: 'network', message: error.message };
  }
}

/**
 * Message handler from popup and content scripts
 */
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  switch (message.type) {
    case 'GET_RECORDING_STATUS':
      sendResponse({
        isRecording,
        currentWorkflow: currentWorkflow ? {
          name: currentWorkflow.name,
          actionsCount: currentWorkflow.actions.length,
          statesCount: currentWorkflow.states.length,
          duration: Date.now() - recordingStartTime
        } : null
      });
      break;

    case 'START_RECORDING':
      startRecording(message.data.workflowName, message.data.projectId);
      sendResponse({ success: true });
      break;

    case 'STOP_RECORDING':
      const workflow = stopRecording();
      sendResponse({ success: true, workflow });
      break;

    case 'SYNC_WORKFLOW':
      syncWorkflow(message.data.workflow).then(result => {
        sendResponse(result);
      });
      return true; // Keep message channel open for async response

    case 'ADD_ACTION':
      addAction(message.data);
      sendResponse({ success: true });
      break;

    case 'ADD_STATE':
      addState(message.data);
      sendResponse({ success: true });
      break;

    default:
      sendResponse({ success: false, error: 'Unknown message type' });
  }
});

// Initialize on install
chrome.runtime.onInstalled.addListener(() => {
  console.log('🚀 Workflow Capture Extension installed');

  // Set default API URL
  chrome.storage.sync.set({
    apiUrl: DEFAULT_API_URL,
    projectId: DEFAULT_PROJECT_ID
  });
});

console.log('👁️ Workflow Capture Extension loaded');
