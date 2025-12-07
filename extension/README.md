# Workflow Manager - Browser Extension

Browser extension for capturing user workflows and synchronizing them with the Workflow Manager backend.

## Features

- 🎬 **Record User Workflows**: Capture clicks, inputs, navigation, and form submissions
- 🔄 **Auto-Sync**: Automatically sync workflows to backend API
- 🔍 **Duplicate Detection**: Hash-based duplicate prevention
- ⚙️ **Configurable**: Set custom API endpoint and project ID
- 🎨 **Visual Feedback**: Recording indicator shows capture is active

## Installation

### For Development

1. Open Chrome/Edge and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select the `extension` directory from this project
5. The extension icon should appear in your toolbar

### For Firefox

1. Open Firefox and navigate to `about:debugging#/runtime/this-firefox`
2. Click "Load Temporary Add-on"
3. Select the `manifest.json` file from the `extension` directory

## Usage

### 1. Configure Settings

1. Click the extension icon in your browser toolbar
2. Click "⚙️ Settings" at the bottom
3. Set your **API URL** (default: `http://localhost:8001/api/v1`)
4. Click "Save Settings"

### 2. Start Recording a Workflow

1. Navigate to the web page where you want to capture a workflow
2. Click the extension icon
3. Enter a **Workflow Name** (e.g., "User Login Flow")
4. Set the **Project ID** (must exist in backend)
5. Click "▶️ Start Recording"

**Note**: A red "Recording Workflow" indicator will appear in the top-right of the page.

### 3. Perform Actions

With recording active, perform the workflow steps:
- Click buttons, links
- Fill in form fields
- Submit forms
- Navigate between pages

All actions are automatically captured.

### 4. Stop Recording

1. Click the extension icon
2. Click "⏹️ Stop Recording"
3. Review the captured workflow summary

### 5. Sync to Server

1. Click "🔄 Sync to Server"
2. The workflow will be sent to the backend API
3. You'll see a success/error message

**Duplicate Detection**: If a workflow with the same hash already exists, you'll get a warning and the workflow won't be created.

## Captured Data

The extension captures the following information:

### Actions
- **Clicks**: Element clicked (tag, id, classes, text, href, xpath)
- **Inputs**: Form field interactions (without actual input values for security)
- **Form Submissions**: Form metadata (action, method, field count)

### States
- **Page Views**: URL, title, timestamp
- **Page Unloads**: Navigation events

### Metadata
- Workflow name and description
- Start/end time and duration
- Current page URL and domain
- User agent

## Configuration

### API URL

By default, the extension connects to `http://localhost:8001/api/v1`.

To change this:
1. Click Settings
2. Update the API URL field
3. Save

### Project ID

Each workflow must be associated with a project. Make sure the Project ID exists in your backend before recording.

## Security & Privacy

- **No Password Capture**: Password fields are automatically excluded
- **Input Redaction**: Text input values are redacted as `[REDACTED]`
- **Local Storage**: API settings are stored in Chrome sync storage
- **CORS**: Ensure your backend allows requests from the browser extension

## Backend API Requirements

The extension expects the following endpoint:

```
POST /api/v1/workflows/
Content-Type: application/json

{
  "name": "Workflow Name",
  "project_id": 1,
  "description": "...",
  "url": "https://example.com",
  "domain": "example.com",
  "duration_ms": 15000,
  "workflow_hash": "abc123",
  "raw_data": { ... },
  "states": [ ... ],
  "actions": [ ... ]
}
```

See `backend/app/schemas/workflow.py` for complete schema.

## Troubleshooting

### Extension Not Capturing Events

- Make sure recording is started (red indicator visible)
- Check console for errors (F12 → Console)
- Verify content script is loaded

### Sync Failed

- Verify backend is running: `curl http://localhost:8001/health`
- Check API URL in extension settings
- Verify project ID exists in backend
- Check backend logs for errors: `docker compose logs -f backend`

### Duplicate Workflow Error

This means a workflow with the same hash already exists. The hash is based on:
- URL
- Domain
- Action types sequence
- State types sequence

You can either:
- Record a different workflow
- Delete the existing workflow in the backend
- Modify the workflow slightly (add/remove an action)

## Development

### File Structure

```
extension/
├── manifest.json       # Extension configuration
├── background.js       # Service worker (workflow management)
├── content.js          # Content script (event capture)
├── popup.html          # Popup UI
├── popup.css           # Popup styles
├── popup.js            # Popup logic
└── icons/              # Extension icons
```

### Testing

1. Load extension in developer mode
2. Open browser console: Extension page → "Inspect views: service worker"
3. Open page console: F12 → Console
4. Watch for log messages during recording

### Debugging

- **Background script logs**: Extension page → Service Worker → Inspect
- **Content script logs**: Web page → F12 → Console
- **Popup logs**: Right-click extension icon → Inspect popup

## Known Limitations

- Single tab recording (doesn't track multi-tab workflows)
- No iframe capture
- No dynamic SPA state tracking (e.g., React state changes)
- Simple hash function (not cryptographically secure)

## Future Enhancements

- [ ] Multi-tab workflow support
- [ ] Enhanced SPA support (React, Vue, Angular)
- [ ] Screenshot capture at key steps
- [ ] Workflow replay functionality
- [ ] Advanced filtering (exclude certain events)
- [ ] Offline storage and batch sync
- [ ] Workflow templates and suggestions

## License

MIT - See root LICENSE file
