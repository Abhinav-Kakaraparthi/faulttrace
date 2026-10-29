"""Explicit LangSmith project OR agent routing; no SDK or secret projection."""
import os
import re
import uuid

ENDPOINTS = {
    'https://api.smith.langchain.com', 'https://eu.api.smith.langchain.com',
    'https://apac.api.smith.langchain.com', 'https://aws.api.smith.langchain.com',
}


def configuration():
    endpoint = os.environ.get('LANGSMITH_ENDPOINT', 'https://api.smith.langchain.com').rstrip('/')
    if endpoint not in ENDPOINTS:
        raise ValueError('invalid_trace_endpoint')
    project = os.environ.get('LANGSMITH_PROJECT')
    agent = os.environ.get('LANGSMITH_AGENT_ID')
    environment = os.environ.get('LANGSMITH_AGENT_ENVIRONMENT')
    if agent or environment:
        if project:
            raise ValueError('conflicting_trace_destinations')
        if not isinstance(agent, str) or not re.fullmatch(r'[a-z](?:[a-z0-9-]{0,61}[a-z0-9])?', agent):
            raise ValueError('invalid_trace_agent')
        if not isinstance(environment, str) or environment.lower() not in ('local', 'development', 'staging', 'production'):
            raise ValueError('invalid_trace_environment')
        destination = {'address': f'lrn:agents/{agent}/environments/{environment.lower()}'}
    elif isinstance(project, str) and re.fullmatch(r'[A-Za-z0-9_-]{1,64}', project):
        destination = {'session_name': project}
    else:
        raise ValueError('missing_trace_destination')
    headers = {}
    workspace = os.environ.get('LANGSMITH_WORKSPACE_ID')
    if workspace:
        try:
            headers['x-tenant-id'] = str(uuid.UUID(workspace))
        except (ValueError, TypeError, AttributeError):
            raise ValueError('invalid_trace_workspace') from None
    return endpoint, headers, destination
