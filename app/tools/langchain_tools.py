from langchain.tools import tool

from app.tools.repository_inspector import inspect_repository


@tool
def inspect_github_repository(github_url:str) -> dict:
    """Inspect a public GitHub repository to identify project files,
    dependency manifests, Docker configuration, tests, and GitHub
    Actions workflows. Use this before planning a deployment when
    repository information is not already available."""

    return inspect_repository(github_url)

