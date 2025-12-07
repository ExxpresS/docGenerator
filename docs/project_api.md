# Project API Documentation

This document provides comprehensive documentation for the Project API endpoints available in the docGenerator application.

## Base URL

All API endpoints are prefixed with `/api/v1/projects`.

## Authentication

Authentication requirements are not specified in the current implementation. Please refer to the application's authentication documentation for details.

## Endpoints

### Create a Project

Creates a new project in the system.

**URL**: `/`

**Method**: `POST`

**Request Body**:

```json
{
  "name": "Sample Project",
  "description": "This is a sample project"
}
```

**Response**: `201 Created`

```json
{
  "id": 1,
  "name": "Sample Project",
  "description": "This is a sample project",
  "created_at": "2023-06-15T10:00:00Z",
  "updated_at": "2023-06-15T10:00:00Z"
}
```

**Error Responses**:
- `500 Internal Server Error`: If there's an error creating the project

### Get All Projects

Retrieves all projects in the system.

**URL**: `/`

**Method**: `GET`

**Query Parameters**:
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum number of records to return (default: 100)

**Response**: `200 OK`

```json
[
  {
    "id": 1,
    "name": "Sample Project",
    "description": "This is a sample project",
    "created_at": "2023-06-15T10:00:00Z",
    "updated_at": "2023-06-15T10:00:00Z"
  }
]
```

**Error Responses**:
- `500 Internal Server Error`: If there's an error fetching the projects

### Get Project by ID

Retrieves a specific project by its ID.

**URL**: `/{project_id}`

**Method**: `GET`

**URL Parameters**:
- `project_id`: ID of the project

**Response**: `200 OK`

```json
{
  "id": 1,
  "name": "Sample Project",
  "description": "This is a sample project",
  "created_at": "2023-06-15T10:00:00Z",
  "updated_at": "2023-06-15T10:00:00Z"
}
```

**Error Responses**:
- `404 Not Found`: If the specified project_id does not exist
- `500 Internal Server Error`: If there's an error fetching the project

### Update Project

Updates an existing project.

**URL**: `/{project_id}`

**Method**: `PUT`

**URL Parameters**:
- `project_id`: ID of the project to update

**Request Body**:

```json
{
  "name": "Updated Project Name",
  "description": "Updated project description"
}
```

**Response**: `200 OK`

```json
{
  "id": 1,
  "name": "Updated Project Name",
  "description": "Updated project description",
  "created_at": "2023-06-15T10:00:00Z",
  "updated_at": "2023-06-15T11:00:00Z"
}
```

**Error Responses**:
- `404 Not Found`: If the specified project_id does not exist
- `500 Internal Server Error`: If there's an error updating the project

### Delete Project

Deletes a project.

**URL**: `/{project_id}`

**Method**: `DELETE`

**URL Parameters**:
- `project_id`: ID of the project to delete

**Response**: `204 No Content`

**Error Responses**:
- `404 Not Found`: If the specified project_id does not exist
- `500 Internal Server Error`: If there's an error deleting the project

### Get Project Statistics

Retrieves statistics for a specific project.

**URL**: `/{project_id}/stats`

**Method**: `GET`

**URL Parameters**:
- `project_id`: ID of the project

**Response**: `200 OK`

```json
{
  "project_id": 1,
  "workflow_count": 5
}
```

**Error Responses**:
- `404 Not Found`: If the specified project_id does not exist
- `500 Internal Server Error`: If there's an error fetching the project statistics

## Data Models

### Project

| Field | Type | Description |
|-------|------|-------------|
| id | integer | Unique identifier for the project |
| name | string | Name of the project (1-255 characters) |
| description | string | Optional description of the project |
| created_at | datetime | When the project was created |
| updated_at | datetime | When the project was last updated |
