# Document API Documentation

This document provides comprehensive documentation for the Document API endpoints available in the docGenerator application.

## Base URL

All API endpoints are prefixed with `/api/v1/documents`.

## Authentication

Authentication requirements are not specified in the current implementation. Please refer to the application's authentication documentation for details.

## Document Status Workflow

Documents in the system follow a status workflow:

1. **DRAFT** - Initial status when a document is created
2. **VALIDATED** - Document has been validated
3. **PUBLISHED** - Document has been published

## Content Types

Documents can have the following content types:

- **markdown** - Markdown formatted text
- **json** - JSON formatted data
- **html** - HTML formatted content

## Endpoints

### Document CRUD Operations

#### Create a Document

Creates a new document manually.

**URL**: `/`

**Method**: `POST`

**Request Body**:

```json
{
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
}
```

**Response**: `201 Created`

```json
{
  "id": 1,
  "project_id": 1,
  "workflow_id": 2,
  "title": "API Documentation",
  "content": "# API Documentation\n\nThis is a sample document.",
  "content_type": "markdown",
  "status": "draft",
  "is_indexed": false,
  "metadata": {
    "author": "John Doe",
    "version": "1.0"
  },
  "version": 1,
  "created_at": "2023-06-15T10:00:00Z",
  "updated_at": "2023-06-15T10:00:00Z",
  "validated_at": null,
  "last_indexed_at": null,
  "chunks_count": 0
}
```

**Error Responses**:
- `500 Internal Server Error`: If there's an error creating the document

#### Get All Documents

Retrieves all documents with optional filters.

**URL**: `/`

**Method**: `GET`

**Query Parameters**:
- `status`: Filter by document status (draft, validated, published)
- `limit`: Maximum number of records to return (default: 100, max: 500)
- `offset`: Number of records to skip (default: 0)

**Response**: `200 OK`

```json
[
  {
    "id": 1,
    "project_id": 1,
    "workflow_id": 2,
    "title": "API Documentation",
    "content": "# API Documentation\n\nThis is a sample document.",
    "content_type": "markdown",
    "status": "draft",
    "is_indexed": false,
    "metadata": {
      "author": "John Doe",
      "version": "1.0"
    },
    "version": 1,
    "created_at": "2023-06-15T10:00:00Z",
    "updated_at": "2023-06-15T10:00:00Z",
    "validated_at": null,
    "last_indexed_at": null,
    "chunks_count": 0
  }
]
```

**Error Responses**:
- `500 Internal Server Error`: If there's an error fetching the documents

#### Get Document by ID

Retrieves a specific document by its ID.

**URL**: `/{document_id}`

**Method**: `GET`

**URL Parameters**:
- `document_id`: ID of the document

**Response**: `200 OK`

```json
{
  "id": 1,
  "project_id": 1,
  "workflow_id": 2,
  "title": "API Documentation",
  "content": "# API Documentation\n\nThis is a sample document.",
  "content_type": "markdown",
  "status": "draft",
  "is_indexed": false,
  "metadata": {
    "author": "John Doe",
    "version": "1.0"
  },
  "version": 1,
  "created_at": "2023-06-15T10:00:00Z",
  "updated_at": "2023-06-15T10:00:00Z",
  "validated_at": null,
  "last_indexed_at": null,
  "chunks_count": 0
}
```

**Error Responses**:
- `404 Not Found`: If the specified document_id does not exist
- `500 Internal Server Error`: If there's an error fetching the document

#### Update Document

Updates an existing document. Creates a new version if content changes.

**URL**: `/{document_id}`

**Method**: `PUT`

**URL Parameters**:
- `document_id`: ID of the document to update

**Request Body**:

```json
{
  "title": "Updated API Documentation",
  "content": "# Updated API Documentation\n\nThis is an updated document.",
  "content_type": "markdown",
  "status": "validated",
  "metadata": {
    "author": "John Doe",
    "version": "1.1"
  }
}
```

**Response**: `200 OK`

```json
{
  "id": 1,
  "project_id": 1,
  "workflow_id": 2,
  "title": "Updated API Documentation",
  "content": "# Updated API Documentation\n\nThis is an updated document.",
  "content_type": "markdown",
  "status": "validated",
  "is_indexed": false,
  "metadata": {
    "author": "John Doe",
    "version": "1.1"
  },
  "version": 2,
  "created_at": "2023-06-15T10:00:00Z",
  "updated_at": "2023-06-15T11:00:00Z",
  "validated_at": "2023-06-15T11:00:00Z",
  "last_indexed_at": null,
  "chunks_count": 0
}
```

**Error Responses**:
- `404 Not Found`: If the specified document_id does not exist
- `500 Internal Server Error`: If there's an error updating the document

#### Delete Document

Deletes a document (cascade deletes versions and chunks).

**URL**: `/{document_id}`

**Method**: `DELETE`

**URL Parameters**:
- `document_id`: ID of the document to delete

**Response**: `204 No Content`

**Error Responses**:
- `404 Not Found`: If the specified document_id does not exist
- `500 Internal Server Error`: If there's an error deleting the document

### Document Generation

#### Generate Document from Workflow

Generates a document from a workflow.

**URL**: `/generate`

**Method**: `POST`

**Request Body**:

```json
{
  "workflow_id": 1,
  "title": "Generated Documentation",
  "content_type": "markdown",
  "auto_validate": false
}
```

**Response**: `201 Created`

```json
{
  "id": 1,
  "project_id": 1,
  "workflow_id": 1,
  "title": "Generated Documentation",
  "content": "# Generated Documentation\n\nThis is a generated document.",
  "content_type": "markdown",
  "status": "draft",
  "is_indexed": false,
  "metadata": {
    "generated": true,
    "generation_date": "2023-06-15T10:00:00Z"
  },
  "version": 1,
  "created_at": "2023-06-15T10:00:00Z",
  "updated_at": "2023-06-15T10:00:00Z",
  "validated_at": null,
  "last_indexed_at": null,
  "chunks_count": 0
}
```

**Error Responses**:
- `404 Not Found`: If the specified workflow_id does not exist
- `500 Internal Server Error`: If there's an error generating the document

### Document Status Workflow

#### Validate Document

Changes document status to 'validated'.

**URL**: `/{document_id}/validate`

**Method**: `POST`

**URL Parameters**:
- `document_id`: ID of the document to validate

**Response**: `200 OK`

```json
{
  "id": 1,
  "project_id": 1,
  "workflow_id": 2,
  "title": "API Documentation",
  "content": "# API Documentation\n\nThis is a sample document.",
  "content_type": "markdown",
  "status": "validated",
  "is_indexed": false,
  "metadata": {
    "author": "John Doe",
    "version": "1.0"
  },
  "version": 1,
  "created_at": "2023-06-15T10:00:00Z",
  "updated_at": "2023-06-15T10:00:00Z",
  "validated_at": "2023-06-15T11:00:00Z",
  "last_indexed_at": null,
  "chunks_count": 0
}
```

**Error Responses**:
- `404 Not Found`: If the specified document_id does not exist
- `500 Internal Server Error`: If there's an error validating the document

#### Publish Document

Changes document status to 'published'.

**URL**: `/{document_id}/publish`

**Method**: `POST`

**URL Parameters**:
- `document_id`: ID of the document to publish

**Response**: `200 OK`

```json
{
  "id": 1,
  "project_id": 1,
  "workflow_id": 2,
  "title": "API Documentation",
  "content": "# API Documentation\n\nThis is a sample document.",
  "content_type": "markdown",
  "status": "published",
  "is_indexed": false,
  "metadata": {
    "author": "John Doe",
    "version": "1.0"
  },
  "version": 1,
  "created_at": "2023-06-15T10:00:00Z",
  "updated_at": "2023-06-15T10:00:00Z",
  "validated_at": "2023-06-15T11:00:00Z",
  "last_indexed_at": null,
  "chunks_count": 0
}
```

**Error Responses**:
- `404 Not Found`: If the specified document_id does not exist
- `500 Internal Server Error`: If there's an error publishing the document

### Document Versions

#### Get Document Versions

Retrieves all versions of a document.

**URL**: `/{document_id}/versions`

**Method**: `GET`

**URL Parameters**:
- `document_id`: ID of the document

**Response**: `200 OK`

```json
[
  {
    "id": 1,
    "document_id": 1,
    "content": "# API Documentation\n\nThis is a sample document.",
    "version_number": 1,
    "change_summary": "Initial version",
    "created_at": "2023-06-15T10:00:00Z"
  },
  {
    "id": 2,
    "document_id": 1,
    "content": "# Updated API Documentation\n\nThis is an updated document.",
    "version_number": 2,
    "change_summary": "Updated via API",
    "created_at": "2023-06-15T11:00:00Z"
  }
]
```

**Error Responses**:
- `404 Not Found`: If the specified document_id does not exist
- `500 Internal Server Error`: If there's an error fetching the document versions

#### Get Document Version

Retrieves a specific version of a document.

**URL**: `/{document_id}/versions/{version_number}`

**Method**: `GET`

**URL Parameters**:
- `document_id`: ID of the document
- `version_number`: Version number to retrieve

**Response**: `200 OK`

```json
{
  "id": 1,
  "document_id": 1,
  "content": "# API Documentation\n\nThis is a sample document.",
  "version_number": 1,
  "change_summary": "Initial version",
  "created_at": "2023-06-15T10:00:00Z"
}
```

**Error Responses**:
- `404 Not Found`: If the specified document_id or version_number does not exist
- `500 Internal Server Error`: If there's an error fetching the document version

#### Get Document with Versions

Retrieves a document with all its versions.

**URL**: `/{document_id}/with-versions`

**Method**: `GET`

**URL Parameters**:
- `document_id`: ID of the document

**Response**: `200 OK`

```json
{
  "id": 1,
  "project_id": 1,
  "workflow_id": 2,
  "title": "API Documentation",
  "content": "# API Documentation\n\nThis is a sample document.",
  "content_type": "markdown",
  "status": "draft",
  "is_indexed": false,
  "metadata": {
    "author": "John Doe",
    "version": "1.0"
  },
  "version": 1,
  "created_at": "2023-06-15T10:00:00Z",
  "updated_at": "2023-06-15T10:00:00Z",
  "validated_at": null,
  "last_indexed_at": null,
  "chunks_count": 0,
  "versions": [
    {
      "id": 1,
      "document_id": 1,
      "content": "# API Documentation\n\nThis is a sample document.",
      "version_number": 1,
      "change_summary": "Initial version",
      "created_at": "2023-06-15T10:00:00Z"
    }
  ]
}
```

**Error Responses**:
- `404 Not Found`: If the specified document_id does not exist
- `500 Internal Server Error`: If there's an error fetching the document with versions

### Project-Specific Endpoints

#### Get Documents by Project

Retrieves all documents for a specific project.

**URL**: `/by-project/{project_id}`

**Method**: `GET`

**URL Parameters**:
- `project_id`: ID of the project

**Query Parameters**:
- `status`: Filter by document status (draft, validated, published)
- `limit`: Maximum number of records to return (default: 100, max: 500)
- `offset`: Number of records to skip (default: 0)

**Response**: `200 OK`

```json
[
  {
    "id": 1,
    "project_id": 1,
    "workflow_id": 2,
    "title": "API Documentation",
    "content": "# API Documentation\n\nThis is a sample document.",
    "content_type": "markdown",
    "status": "draft",
    "is_indexed": false,
    "metadata": {
      "author": "John Doe",
      "version": "1.0"
    },
    "version": 1,
    "created_at": "2023-06-15T10:00:00Z",
    "updated_at": "2023-06-15T10:00:00Z",
    "validated_at": null,
    "last_indexed_at": null,
    "chunks_count": 0
  }
]
```

**Error Responses**:
- `500 Internal Server Error`: If there's an error fetching the documents

#### Generate Project Summary

Generates a summary document for all workflows in a project.

**URL**: `/generate-project-summary/{project_id}`

**Method**: `POST`

**URL Parameters**:
- `project_id`: ID of the project

**Query Parameters**:
- `title`: Optional title for the generated document

**Response**: `201 Created`

```json
{
  "id": 1,
  "project_id": 1,
  "workflow_id": null,
  "title": "Project Summary",
  "content": "# Project Summary\n\nThis is a summary of all workflows in the project.",
  "content_type": "markdown",
  "status": "draft",
  "is_indexed": false,
  "metadata": {
    "generated": true,
    "generation_date": "2023-06-15T10:00:00Z",
    "summary_type": "project"
  },
  "version": 1,
  "created_at": "2023-06-15T10:00:00Z",
  "updated_at": "2023-06-15T10:00:00Z",
  "validated_at": null,
  "last_indexed_at": null,
  "chunks_count": 0
}
```

**Error Responses**:
- `404 Not Found`: If the specified project_id does not exist
- `500 Internal Server Error`: If there's an error generating the project summary

#### Get Document Statistics

Retrieves document statistics for a project.

**URL**: `/stats/by-project/{project_id}`

**Method**: `GET`

**URL Parameters**:
- `project_id`: ID of the project

**Response**: `200 OK`

```json
{
  "total_documents": 5,
  "by_status": {
    "draft": 2,
    "validated": 2,
    "published": 1
  },
  "by_content_type": {
    "markdown": 3,
    "html": 1,
    "json": 1
  },
  "average_versions": 2.5
}
```

**Error Responses**:
- `500 Internal Server Error`: If there's an error fetching the document statistics

## Data Models

### Document

| Field | Type | Description |
|-------|------|-------------|
| id | integer | Unique identifier for the document |
| project_id | integer | ID of the project this document belongs to |
| workflow_id | integer | Optional ID of the workflow this document was generated from |
| title | string | Title of the document (1-255 characters) |
| content | string | Content of the document |
| content_type | string | Type of content (markdown, json, html) |
| status | string | Status of the document (draft, validated, published) |
| is_indexed | boolean | Whether the document has been indexed for search |
| metadata | object | Optional metadata associated with the document |
| version | integer | Current version number of the document |
| created_at | datetime | When the document was created |
| updated_at | datetime | When the document was last updated |
| validated_at | datetime | When the document was validated (null if not validated) |
| last_indexed_at | datetime | When the document was last indexed (null if not indexed) |
| chunks_count | integer | Number of chunks the document has been split into for indexing |

### DocumentVersion

| Field | Type | Description |
|-------|------|-------------|
| id | integer | Unique identifier for the document version |
| document_id | integer | ID of the document this version belongs to |
| content | string | Content of the document at this version |
| version_number | integer | Version number |
| change_summary | string | Optional summary of changes in this version |
| created_at | datetime | When the version was created |
