# docGenerator API Documentation

This documentation provides a comprehensive guide to the docGenerator API, which allows clients to interact with the workflow management system.

## Overview

The docGenerator API is a RESTful API that allows clients to manage projects, workflows, and documents. The API is organized into the following resources:

- **Projects**: Create, read, update, and delete projects
- **Workflows**: Create, read, update, and delete workflows associated with projects
- **Documents**: Create, read, update, delete, and generate documents from workflows

## API Endpoints

The API is versioned, with all endpoints prefixed with `/api/v1`.

### Project Endpoints

Projects are the top-level organizational unit in the docGenerator system. Each project can contain multiple workflows.

[Detailed Project API Documentation](project_api.md)

### Workflow Endpoints

Workflows represent user interactions captured by the system. Each workflow belongs to a project and contains states and actions.

[Detailed Workflow API Documentation](workflow_api.md)

### Document Endpoints

Documents are generated from workflows or created manually. They can be in different formats (markdown, HTML, JSON) and follow a status workflow (draft, validated, published).

[Detailed Document API Documentation](document_api.md)

## Authentication

Authentication requirements are not specified in the current implementation. Please refer to the application's authentication documentation for details.

## Common Response Codes

| Code | Description |
|------|-------------|
| 200 | OK - The request was successful |
| 201 | Created - A new resource was successfully created |
| 204 | No Content - The request was successful but there is no content to return |
| 400 | Bad Request - The request was malformed or invalid |
| 404 | Not Found - The requested resource was not found |
| 409 | Conflict - The request could not be completed due to a conflict with the current state of the resource |
| 500 | Internal Server Error - An error occurred on the server |

## Data Models

### Project

A project is the top-level organizational unit in the docGenerator system.

[Project Data Model](project_api.md#data-models)

### Workflow

A workflow represents a user interaction captured by the system.

[Workflow Data Model](workflow_api.md#data-models)

### Document

A document is generated from a workflow or created manually, and can be versioned.

[Document Data Model](document_api.md#data-models)

## Examples

### Creating a Project

```bash
curl -X POST "http://localhost:8000/api/v1/projects/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sample Project",
    "description": "This is a sample project"
  }'
```

### Creating a Workflow

```bash
curl -X POST "http://localhost:8000/api/v1/workflows/" \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
```

### Creating a Document

```bash
curl -X POST "http://localhost:8000/api/v1/documents/" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "workflow_id": 2,
    "title": "API Documentation",
    "content": "# API Documentation\n\nThis is a sample document.",
    "content_type": "markdown",
    "status": "draft",
    "metadata": {
      "author": "John Doe",
      "version": "1.0"
    }
  }'
```

### Generating a Document from a Workflow

```bash
curl -X POST "http://localhost:8000/api/v1/documents/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": 1,
    "title": "Generated Documentation",
    "content_type": "markdown",
    "auto_validate": false
  }'
```

## Rate Limiting

Rate limiting information is not specified in the current implementation.

## Pagination

The API supports pagination for endpoints that return multiple resources. Use the `skip` and `limit` query parameters to control pagination.

Example:
```
GET /api/v1/projects/?skip=0&limit=10
```

This will return the first 10 projects.
