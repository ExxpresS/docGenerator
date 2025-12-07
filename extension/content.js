/**
 * Content Script for Workflow Capture
 * Injected into web pages to capture user interactions
 */

let isCapturing = false;
let captureOverlay = null;

/**
 * Create visual indicator that recording is active
 */
function createRecordingIndicator() {
  const indicator = document.createElement('div');
  indicator.id = 'workflow-recording-indicator';
  indicator.innerHTML = `
    <div style="
      position: fixed;
      top: 10px;
      right: 10px;
      background: #e74c3c;
      color: white;
      padding: 8px 16px;
      border-radius: 20px;
      font-family: Arial, sans-serif;
      font-size: 14px;
      font-weight: bold;
      z-index: 999999;
      box-shadow: 0 2px 8px rgba(0,0,0,0.3);
      display: flex;
      align-items: center;
      gap: 8px;
    ">
      <span style="
        width: 8px;
        height: 8px;
        background: white;
        border-radius: 50%;
        animation: pulse 1.5s ease-in-out infinite;
      "></span>
      Recording Workflow
    </div>
    <style>
      @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
      }
    </style>
  `;
  document.body.appendChild(indicator);
  return indicator;
}

/**
 * Remove recording indicator
 */
function removeRecordingIndicator() {
  const indicator = document.getElementById('workflow-recording-indicator');
  if (indicator) {
    indicator.remove();
  }
}

/**
 * Capture click events
 */
function handleClick(event) {
  if (!isCapturing) return;

  const target = event.target;
  const action = {
    type: 'click',
    data: {
      tag: target.tagName,
      id: target.id || null,
      classes: Array.from(target.classList),
      text: target.innerText ? target.innerText.substring(0, 100) : null,
      href: target.href || null,
      xpath: getXPath(target),
      timestamp: Date.now(),
      pageUrl: window.location.href
    }
  };

  // Send to background script
  chrome.runtime.sendMessage({
    type: 'ADD_ACTION',
    data: action
  });

  console.log('🖱️ Click captured:', action);
}

/**
 * Capture input events
 */
function handleInput(event) {
  if (!isCapturing) return;

  const target = event.target;

  // Don't capture password fields for security
  if (target.type === 'password') return;

  const action = {
    type: 'input',
    data: {
      tag: target.tagName,
      id: target.id || null,
      name: target.name || null,
      type: target.type || null,
      value: target.type === 'text' || target.type === 'email' ? '[REDACTED]' : target.value,
      placeholder: target.placeholder || null,
      xpath: getXPath(target),
      timestamp: Date.now(),
      pageUrl: window.location.href
    }
  };

  chrome.runtime.sendMessage({
    type: 'ADD_ACTION',
    data: action
  });

  console.log('⌨️ Input captured:', action);
}

/**
 * Capture navigation events
 */
function handleNavigation() {
  if (!isCapturing) return;

  const state = {
    type: 'page_view',
    data: {
      url: window.location.href,
      title: document.title,
      timestamp: Date.now(),
      referrer: document.referrer
    }
  };

  chrome.runtime.sendMessage({
    type: 'ADD_STATE',
    data: state
  });

  console.log('🌐 Navigation captured:', state);
}

/**
 * Capture form submissions
 */
function handleSubmit(event) {
  if (!isCapturing) return;

  const form = event.target;
  const action = {
    type: 'form_submit',
    data: {
      id: form.id || null,
      action: form.action || null,
      method: form.method || null,
      fieldCount: form.elements.length,
      xpath: getXPath(form),
      timestamp: Date.now(),
      pageUrl: window.location.href
    }
  };

  chrome.runtime.sendMessage({
    type: 'ADD_ACTION',
    data: action
  });

  console.log('📝 Form submit captured:', action);
}

/**
 * Get XPath of an element
 */
function getXPath(element) {
  if (element.id) {
    return `//*[@id="${element.id}"]`;
  }

  if (element === document.body) {
    return '/html/body';
  }

  let ix = 0;
  const siblings = element.parentNode ? element.parentNode.childNodes : [];

  for (let i = 0; i < siblings.length; i++) {
    const sibling = siblings[i];
    if (sibling === element) {
      const parentPath = element.parentNode ? getXPath(element.parentNode) : '';
      return `${parentPath}/${element.tagName.toLowerCase()}[${ix + 1}]`;
    }
    if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {
      ix++;
    }
  }

  return '';
}

/**
 * Start capturing events
 */
function startCapture() {
  if (isCapturing) return;

  isCapturing = true;

  // Add event listeners
  document.addEventListener('click', handleClick, true);
  document.addEventListener('input', handleInput, true);
  document.addEventListener('submit', handleSubmit, true);

  // Capture initial page view
  handleNavigation();

  // Show recording indicator
  captureOverlay = createRecordingIndicator();

  console.log('🎬 Capture started on page:', window.location.href);
}

/**
 * Stop capturing events
 */
function stopCapture() {
  if (!isCapturing) return;

  isCapturing = false;

  // Remove event listeners
  document.removeEventListener('click', handleClick, true);
  document.removeEventListener('input', handleInput, true);
  document.removeEventListener('submit', handleSubmit, true);

  // Remove recording indicator
  removeRecordingIndicator();

  console.log('⏹️ Capture stopped on page:', window.location.href);
}

/**
 * Listen for messages from background script
 */
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  switch (message.type) {
    case 'START_RECORDING':
      startCapture();
      sendResponse({ success: true });
      break;

    case 'STOP_RECORDING':
      stopCapture();
      sendResponse({ success: true });
      break;

    default:
      sendResponse({ success: false });
  }
});

// Capture page unload
window.addEventListener('beforeunload', () => {
  if (isCapturing) {
    const state = {
      type: 'page_unload',
      data: {
        url: window.location.href,
        timestamp: Date.now()
      }
    };

    chrome.runtime.sendMessage({
      type: 'ADD_STATE',
      data: state
    });
  }
});

console.log('👁️ Workflow capture content script loaded');
