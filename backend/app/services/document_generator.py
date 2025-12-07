"""
Document Generator Service
Converts workflow data (JSON) to readable documentation formats (Markdown, HTML, etc.)
"""
from typing import Dict, Any, Optional
import json
from datetime import datetime
from app.db.queries import workflows as workflow_queries
from app.db.queries import documents as document_queries


class DocumentGenerator:
    """Service to generate documentation from workflow data"""

    @staticmethod
    def workflow_to_markdown(workflow_data: Dict[str, Any]) -> str:
        """
        Convert a workflow (with states and actions) to Markdown documentation

        Args:
            workflow_data: Complete workflow data including states and actions

        Returns:
            Markdown formatted documentation string
        """
        workflow = workflow_data
        md = []

        # Header
        md.append(f"# {workflow.get('name', 'Untitled Workflow')}\n")

        # Metadata section
        md.append("## Metadata\n")
        if workflow.get('description'):
            md.append(f"**Description:** {workflow['description']}\n")
        if workflow.get('url'):
            md.append(f"**URL:** {workflow['url']}\n")
        if workflow.get('domain'):
            md.append(f"**Domain:** {workflow['domain']}\n")
        if workflow.get('duration_ms'):
            duration_sec = workflow['duration_ms'] / 1000
            md.append(f"**Duration:** {duration_sec:.2f}s ({workflow['duration_ms']}ms)\n")
        if workflow.get('created_at'):
            md.append(f"**Captured:** {workflow['created_at']}\n")
        md.append("\n")

        # Overview section
        states = workflow.get('states', [])
        actions = workflow.get('actions', [])

        md.append("## Overview\n")
        md.append(f"- **Total States:** {len(states)}\n")
        md.append(f"- **Total Actions:** {len(actions)}\n")
        md.append(f"- **Workflow Hash:** `{workflow.get('workflow_hash', 'N/A')}`\n")
        md.append("\n")

        # States section
        if states:
            md.append("## States\n")
            for idx, state in enumerate(states, 1):
                state_type = state.get('state_type', 'unknown')
                md.append(f"### State {idx}: {state_type}\n")

                if state.get('timestamp'):
                    md.append(f"**Timestamp:** {state['timestamp']}\n")

                if state.get('sequence_order') is not None:
                    md.append(f"**Sequence:** {state['sequence_order']}\n")

                # Format state data
                if state.get('state_data'):
                    md.append("\n**State Data:**\n")
                    md.append("```json\n")
                    md.append(json.dumps(state['state_data'], indent=2))
                    md.append("\n```\n")

                md.append("\n")

        # Actions section
        if actions:
            md.append("## Actions\n")
            for idx, action in enumerate(actions, 1):
                action_type = action.get('action_type', 'unknown')
                md.append(f"### Action {idx}: {action_type}\n")

                if action.get('timestamp'):
                    md.append(f"**Timestamp:** {action['timestamp']}\n")

                if action.get('sequence_order') is not None:
                    md.append(f"**Sequence:** {action['sequence_order']}\n")

                # Format action data
                if action.get('action_data'):
                    md.append("\n**Action Data:**\n")
                    md.append("```json\n")
                    md.append(json.dumps(action['action_data'], indent=2))
                    md.append("\n```\n")

                md.append("\n")

        # Raw data section (appendix)
        if workflow.get('raw_data'):
            md.append("## Raw Data (Appendix)\n")
            md.append("Complete raw workflow data as captured:\n\n")
            md.append("```json\n")
            md.append(json.dumps(workflow['raw_data'], indent=2))
            md.append("\n```\n")

        return "".join(md)

    @staticmethod
    def workflow_to_json_string(workflow_data: Dict[str, Any]) -> str:
        """
        Convert workflow to formatted JSON string

        Args:
            workflow_data: Complete workflow data

        Returns:
            JSON formatted string
        """
        return json.dumps(workflow_data, indent=2, default=str)

    @staticmethod
    def generate_document_from_workflow(
        workflow_id: int,
        title: Optional[str] = None,
        content_type: str = "markdown",
        auto_validate: bool = False
    ) -> Dict[str, Any]:
        """
        Generate a document from a workflow

        Args:
            workflow_id: ID of the workflow to document
            title: Optional custom title (defaults to workflow name)
            content_type: Output format (markdown, json)
            auto_validate: If True, set document status to validated

        Returns:
            Created document data

        Raises:
            ValueError: If workflow not found or invalid content_type
        """
        # Get workflow with details
        workflow = workflow_queries.get_workflow_by_id(workflow_id, include_details=True)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        # Generate content based on type
        if content_type == "markdown":
            content = DocumentGenerator.workflow_to_markdown(workflow)
        elif content_type == "json":
            content = DocumentGenerator.workflow_to_json_string(workflow)
        else:
            raise ValueError(f"Unsupported content_type: {content_type}")

        # Determine title
        doc_title = title or f"Documentation: {workflow.get('name', 'Workflow')}"

        # Determine status
        status = "validated" if auto_validate else "draft"

        # Create metadata
        metadata = {
            "generated_from_workflow_id": workflow_id,
            "workflow_name": workflow.get('name'),
            "workflow_url": workflow.get('url'),
            "workflow_domain": workflow.get('domain'),
            "generated_at": datetime.now().isoformat(),
            "generator_version": "1.0",
            "content_type": content_type
        }

        # Create document
        document = document_queries.create_document(
            project_id=workflow['project_id'],
            workflow_id=workflow_id,
            title=doc_title,
            content=content,
            content_type=content_type,
            status=status,
            metadata=metadata
        )

        return document

    @staticmethod
    def generate_summary_document_for_project(
        project_id: int,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a summary document listing all workflows in a project

        Args:
            project_id: ID of the project
            title: Optional custom title

        Returns:
            Created summary document
        """
        from app.db.queries import projects as project_queries

        # Get project
        project = project_queries.get_project_by_id(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        # Get all workflows for project
        workflows = workflow_queries.get_workflows_by_project(project_id)

        # Build markdown summary
        md = []
        md.append(f"# Project Summary: {project['name']}\n")

        if project.get('description'):
            md.append(f"\n{project['description']}\n")

        md.append(f"\n**Created:** {project['created_at']}\n")
        md.append(f"**Total Workflows:** {len(workflows)}\n\n")

        # Group by domain
        domains = {}
        for wf in workflows:
            domain = wf.get('domain', 'Unknown')
            if domain not in domains:
                domains[domain] = []
            domains[domain].append(wf)

        md.append("## Workflows by Domain\n\n")
        for domain, domain_workflows in sorted(domains.items()):
            md.append(f"### {domain}\n\n")
            for wf in domain_workflows:
                md.append(f"- **{wf['name']}**")
                if wf.get('url'):
                    md.append(f" - [{wf['url']}]({wf['url']})")
                if wf.get('description'):
                    md.append(f"\n  - {wf['description']}")
                md.append("\n")
            md.append("\n")

        # Complete workflow list
        md.append("## Complete Workflow List\n\n")
        md.append("| ID | Name | URL | Domain | Captured |\n")
        md.append("|---|---|---|---|---|\n")
        for wf in workflows:
            md.append(f"| {wf['id']} | {wf['name']} | {wf.get('url', 'N/A')} | {wf.get('domain', 'N/A')} | {wf['created_at']} |\n")

        content = "".join(md)

        # Create document
        doc_title = title or f"Summary: {project['name']}"
        metadata = {
            "generated_from_project_id": project_id,
            "project_name": project['name'],
            "workflow_count": len(workflows),
            "generated_at": datetime.now().isoformat(),
            "generator_version": "1.0",
            "content_type": "summary"
        }

        document = document_queries.create_document(
            project_id=project_id,
            workflow_id=None,
            title=doc_title,
            content=content,
            content_type="markdown",
            status="draft",
            metadata=metadata
        )

        return document
