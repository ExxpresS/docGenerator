# Workflow API Documentation

This document provides comprehensive documentation for the Workflow API endpoints available in the docGenerator application.

## Base URL

All API endpoints are prefixed with `/api/v1/workflows`.

## Authentication

Authentication requirements are not specified in the current implementation. Please refer to the application's authentication documentation for details.

## Endpoints

### Create a Workflow

Creates a new workflow in the system.

**URL**: `/`

**Method**: `POST`

**Request Body**:

```json
{
  "project_id": 1,
  "name": "Sample Workflow",
  "description": "This is a sample workflow",
  "raw_data": {
    "key": "value"
  },
  "workflow_hash": "abc123hash",
  "url": "https://example.com/workflow",
  "domain": "example.com",
  "duration_ms": 1500,
  "states": [
    {
      "state_type": "initial",
      "state_data": {
        "key": "value"
      },
      "sequence_order": 1,
      "timestamp": "2023-06-15T10:00:00Z"
    }
  ],
  "actions": [
    {
      "action_type": "click",
      "action_data": {
        "element": "button",
        "selector": "#submit"
      },
      "sequence_order": 1,
      "timestamp": "2023-06-15T10:01:00Z"
    }
  ]
}
```

**Response**: `201 Created`

```json
{
  "id": 1,
  "project_id": 1,
  "name": "Sample Workflow",
  "description": "This is a sample workflow",
  "raw_data": {
    "key": "value"
  },
  "workflow_hash": "abc123hash",
  "url": "https://example.com/workflow",
  "domain": "example.com",
  "duration_ms": 1500,
  "created_at": "2023-06-15T10:05:00Z",
  "updated_at": "2023-06-15T10:05:00Z"
}
```

**Error Responses**:
- `404 Not Found`: If the specified project_id does not exist
- `409 Conflict`: If a workflow with the same hash already exists
- `500 Internal Server Error`: If there's an error creating the workflow

### Get Workflows by Project

Retrieves all workflows associated with a specific project.

**URL**: `/project/{project_id}`

**Method**: `GET`

**URL Parameters**:
- `project_id`: ID of the project

**Query Parameters**:
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum number of records to return (default: 100)

**Response**: `200 OK`

```json
[
  {
    "id": 1,
    "project_id": 1,
    "name": "Sample Workflow",
    "description": "This is a sample workflow",
    "raw_data": {
      "key": "value"
    },
    "workflow_hash": "abc123hash",
    "url": "https://example.com/workflow",
    "domain": "example.com",
    "duration_ms": 1500,
    "created_at": "2023-06-15T10:05:00Z",
    "updated_at": "2023-06-15T10:05:00Z"
  }
]
```

**Error Responses**:
- `404 Not Found`: If the specified project_id does not exist
- `500 Internal Server Error`: If there's an error fetching the workflows

### Get Workflow by ID

Retrieves a specific workflow by its ID.

**URL**: `/{workflow_id}`

**Method**: `GET`

**URL Parameters**:
- `workflow_id`: ID of the workflow

**Query Parameters**:
- `include_details`: Whether to include states and actions (default: true)

**Response**: `200 OK`

```json
{
  "id": 1,
  "project_id": 1,
  "name": "Sample Workflow",
  "description": "This is a sample workflow",
  "raw_data": {
    "key": "value"
  },
  "workflow_hash": "abc123hash",
  "url": "https://example.com/workflow",
  "domain": "example.com",
  "duration_ms": 1500,
  "created_at": "2023-06-15T10:05:00Z",
  "updated_at": "2023-06-15T10:05:00Z",
  "states": [
    {
      "state_type": "initial",
      "state_data": {
        "key": "value"
      },
      "sequence_order": 1,
      "timestamp": "2023-06-15T10:00:00Z"
    }
  ],
  "actions": [
    {
      "action_type": "click",
      "action_data": {
        "element": "button",
        "selector": "#submit"
      },
      "sequence_order": 1,
      "timestamp": "2023-06-15T10:01:00Z"
    }
  ]
}
```

**Error Responses**:
- `404 Not Found`: If the specified workflow_id does not exist
- `500 Internal Server Error`: If there's an error fetching the workflow

### Update Workflow

Updates an existing workflow.

**URL**: `/{workflow_id}`

**Method**: `PUT`

**URL Parameters**:
- `workflow_id`: ID of the workflow to update

**Request Body**:

```json
{
  "name": "Updated Workflow Name",
  "description": "Updated workflow description"
}
```

**Response**: `200 OK`

```json
{
  "id": 1,
  "project_id": 1,
  "name": "Updated Workflow Name",
  "description": "Updated workflow description",
  "raw_data": {
    "key": "value"
  },
  "workflow_hash": "abc123hash",
  "url": "https://example.com/workflow",
  "domain": "example.com",
  "duration_ms": 1500,
  "created_at": "2023-06-15T10:05:00Z",
  "updated_at": "2023-06-15T11:00:00Z"
}
```

**Error Responses**:
- `404 Not Found`: If the specified workflow_id does not exist
- `500 Internal Server Error`: If there's an error updating the workflow

### Delete Workflow

Deletes a workflow.

**URL**: `/{workflow_id}`

**Method**: `DELETE`

**URL Parameters**:
- `workflow_id`: ID of the workflow to delete

**Response**: `204 No Content`

**Error Responses**:
- `404 Not Found`: If the specified workflow_id does not exist
- `500 Internal Server Error`: If there's an error deleting the workflow

## Data Models

### Workflow

| Field | Type | Description |
|-------|------|-------------|
| id | integer | Unique identifier for the workflow |
| project_id | integer | ID of the project this workflow belongs to |
| name | string | Name of the workflow (1-255 characters) |
| description | string | Optional description of the workflow |
| raw_data | object | Raw data associated with the workflow |
| workflow_hash | string | Unique hash for the workflow (max 64 characters) |
| url | string | Optional URL associated with the workflow (max 500 characters) |
| domain | string | Optional domain associated with the workflow (max 255 characters) |
| duration_ms | integer | Optional duration of the workflow in milliseconds |
| created_at | datetime | When the workflow was created |
| updated_at | datetime | When the workflow was last updated |

### WorkflowState

| Field | Type | Description |
|-------|------|-------------|
| state_type | string | Type of the state |
| state_data | object | Data associated with the state |
| sequence_order | integer | Order of the state in the workflow sequence |
| timestamp | datetime | When the state occurred |

### WorkflowAction

| Field | Type | Description |
|-------|------|-------------|
| action_type | string | Type of the action |
| action_data | object | Data associated with the action |
| sequence_order | integer | Order of the action in the workflow sequence |
| timestamp | datetime | When the action occurred |
