import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agent import Tool
from tools.file_tools import (
    file_read, file_write, file_list, file_search,
    file_delete, file_move, file_copy, file_info
)
from tools.github_tools import (
    github_create_repo, github_list_repos, github_create_file,
    github_get_file, github_list_files, github_create_branch,
    github_create_pr, github_create_issue, github_push_directory,
    github_get_user
)
from tools.web_shell_tools import (
    web_search, web_fetch, shell_execute, code_execute, install_package
)
from tools.deploy_tools import (
    deploy_vercel, deploy_heroku, deploy_netlify,
    deploy_github_pages, deploy_docker
)
from tools.backend_tools import (
    backend_create, backend_start, backend_stop, backend_status,
    backend_test, backend_add_route
)


def get_all_tools() -> list:
    """Return all registered tools for the agent."""
    return [
        # File Operations
        Tool(
            name="file_read",
            description="Read contents of a file. Use offset and limit for large files.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file"},
                    "offset": {"type": "integer", "description": "Line offset to start reading", "default": 0},
                    "limit": {"type": "integer", "description": "Max lines to read", "default": 1000}
                },
                "required": ["path"]
            },
            func=file_read
        ),
        Tool(
            name="file_write",
            description="Write or append content to a file. Creates directories if needed.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to write to"},
                    "content": {"type": "string", "description": "Content to write"},
                    "append": {"type": "boolean", "description": "Append instead of overwrite", "default": False}
                },
                "required": ["path", "content"]
            },
            func=file_write
        ),
        Tool(
            name="file_list",
            description="List files in a directory with optional pattern matching.",
            parameters={
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Directory path", "default": "."},
                    "pattern": {"type": "string", "description": "Glob pattern", "default": "*"},
                    "recursive": {"type": "boolean", "description": "Search recursively", "default": False}
                },
                "required": []
            },
            func=file_list
        ),
        Tool(
            name="file_search",
            description="Search for text within files in a directory.",
            parameters={
                "type": "object",
                "properties": {
                    "directory": {"type": "string", "description": "Directory to search"},
                    "query": {"type": "string", "description": "Text to search for"},
                    "file_pattern": {"type": "string", "description": "File pattern filter", "default": "*"}
                },
                "required": ["directory", "query"]
            },
            func=file_search
        ),
        Tool(
            name="file_delete",
            description="Delete a file or directory.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to delete"}
                },
                "required": ["path"]
            },
            func=file_delete
        ),
        Tool(
            name="file_move",
            description="Move or rename a file.",
            parameters={
                "type": "object",
                "properties": {
                    "source": {"type": "string", "description": "Source path"},
                    "destination": {"type": "string", "description": "Destination path"}
                },
                "required": ["source", "destination"]
            },
            func=file_move
        ),
        Tool(
            name="file_copy",
            description="Copy a file.",
            parameters={
                "type": "object",
                "properties": {
                    "source": {"type": "string", "description": "Source path"},
                    "destination": {"type": "string", "description": "Destination path"}
                },
                "required": ["source", "destination"]
            },
            func=file_copy
        ),
        Tool(
            name="file_info",
            description="Get information about a file or directory.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to check"}
                },
                "required": ["path"]
            },
            func=file_info
        ),

        # GitHub Operations
        Tool(
            name="github_create_repo",
            description="Create a new GitHub repository.",
            parameters={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Repository name"},
                    "description": {"type": "string", "description": "Repository description"},
                    "private": {"type": "boolean", "description": "Make private", "default": False}
                },
                "required": ["name"]
            },
            func=github_create_repo
        ),
        Tool(
            name="github_list_repos",
            description="List your GitHub repositories.",
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            },
            func=github_list_repos
        ),
        Tool(
            name="github_create_file",
            description="Create or update a file in a GitHub repository.",
            parameters={
                "type": "object",
                "properties": {
                    "owner": {"type": "string", "description": "Repository owner"},
                    "repo": {"type": "string", "description": "Repository name"},
                    "path": {"type": "string", "description": "File path in repo"},
                    "content": {"type": "string", "description": "File content"},
                    "message": {"type": "string", "description": "Commit message", "default": "Update via OmniAgent"},
                    "branch": {"type": "string", "description": "Branch name", "default": "main"}
                },
                "required": ["owner", "repo", "path", "content"]
            },
            func=github_create_file
        ),
        Tool(
            name="github_get_file",
            description="Get file contents from a GitHub repository.",
            parameters={
                "type": "object",
                "properties": {
                    "owner": {"type": "string", "description": "Repository owner"},
                    "repo": {"type": "string", "description": "Repository name"},
                    "path": {"type": "string", "description": "File path"},
                    "branch": {"type": "string", "description": "Branch", "default": "main"}
                },
                "required": ["owner", "repo", "path"]
            },
            func=github_get_file
        ),
        Tool(
            name="github_list_files",
            description="List files in a GitHub repository directory.",
            parameters={
                "type": "object",
                "properties": {
                    "owner": {"type": "string", "description": "Repository owner"},
                    "repo": {"type": "string", "description": "Repository name"},
                    "path": {"type": "string", "description": "Directory path", "default": ""},
                    "branch": {"type": "string", "description": "Branch", "default": "main"}
                },
                "required": ["owner", "repo"]
            },
            func=github_list_files
        ),
        Tool(
            name="github_create_branch",
            description="Create a new branch in a GitHub repository.",
            parameters={
                "type": "object",
                "properties": {
                    "owner": {"type": "string", "description": "Repository owner"},
                    "repo": {"type": "string", "description": "Repository name"},
                    "branch": {"type": "string", "description": "New branch name"},
                    "from_branch": {"type": "string", "description": "Source branch", "default": "main"}
                },
                "required": ["owner", "repo", "branch"]
            },
            func=github_create_branch
        ),
        Tool(
            name="github_create_pr",
            description="Create a pull request.",
            parameters={
                "type": "object",
                "properties": {
                    "owner": {"type": "string", "description": "Repository owner"},
                    "repo": {"type": "string", "description": "Repository name"},
                    "title": {"type": "string", "description": "PR title"},
                    "head": {"type": "string", "description": "Head branch"},
                    "base": {"type": "string", "description": "Base branch"},
                    "body": {"type": "string", "description": "PR description"}
                },
                "required": ["owner", "repo", "title", "head", "base"]
            },
            func=github_create_pr
        ),
        Tool(
            name="github_create_issue",
            description="Create a GitHub issue.",
            parameters={
                "type": "object",
                "properties": {
                    "owner": {"type": "string", "description": "Repository owner"},
                    "repo": {"type": "string", "description": "Repository name"},
                    "title": {"type": "string", "description": "Issue title"},
                    "body": {"type": "string", "description": "Issue body"},
                    "labels": {"type": "array", "items": {"type": "string"}, "description": "Labels"}
                },
                "required": ["owner", "repo", "title"]
            },
            func=github_create_issue
        ),
        Tool(
            name="github_push_directory",
            description="Push entire local directory to GitHub repository.",
            parameters={
                "type": "object",
                "properties": {
                    "owner": {"type": "string", "description": "Repository owner"},
                    "repo": {"type": "string", "description": "Repository name"},
                    "local_path": {"type": "string", "description": "Local directory path"},
                    "remote_path": {"type": "string", "description": "Remote path prefix", "default": ""},
                    "branch": {"type": "string", "description": "Branch", "default": "main"}
                },
                "required": ["owner", "repo", "local_path"]
            },
            func=github_push_directory
        ),
        Tool(
            name="github_get_user",
            description="Get authenticated GitHub user information.",
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            },
            func=github_get_user
        ),

        # Web & Search
        Tool(
            name="web_search",
            description="Search the web for information.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "num_results": {"type": "integer", "description": "Number of results", "default": 10}
                },
                "required": ["query"]
            },
            func=web_search
        ),
        Tool(
            name="web_fetch",
            description="Fetch content from a URL.",
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to fetch"}
                },
                "required": ["url"]
            },
            func=web_fetch
        ),

        # Shell & Code Execution
        Tool(
            name="shell_execute",
            description="Execute shell commands. Blocked: rm -rf /, mkfs, etc.",
            parameters={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command"},
                    "cwd": {"type": "string", "description": "Working directory"},
                    "timeout": {"type": "integer", "description": "Timeout seconds", "default": 60}
                },
                "required": ["command"]
            },
            func=shell_execute
        ),
        Tool(
            name="code_execute",
            description="Execute Python or JavaScript code safely.",
            parameters={
                "type": "object",
                "properties": {
                    "language": {"type": "string", "description": "Language (python, javascript, node)"},
                    "code": {"type": "string", "description": "Code to execute"},
                    "timeout": {"type": "integer", "description": "Timeout seconds", "default": 30}
                },
                "required": ["language", "code"]
            },
            func=code_execute
        ),
        Tool(
            name="install_package",
            description="Install a package using pip or npm.",
            parameters={
                "type": "object",
                "properties": {
                    "package": {"type": "string", "description": "Package name"},
                    "manager": {"type": "string", "description": "pip or npm", "default": "pip"}
                },
                "required": ["package"]
            },
            func=install_package
        ),

        # Deployment
        Tool(
            name="deploy_vercel",
            description="Deploy project to Vercel. Requires VERCEL_TOKEN.",
            parameters={
                "type": "object",
                "properties": {
                    "project_path": {"type": "string", "description": "Path to project"},
                    "name": {"type": "string", "description": "Project name"},
                    "token": {"type": "string", "description": "Vercel token (optional)"}
                },
                "required": ["project_path"]
            },
            func=deploy_vercel
        ),
        Tool(
            name="deploy_heroku",
            description="Deploy to Heroku. Requires HEROKU_API_KEY.",
            parameters={
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "Heroku app name"},
                    "project_path": {"type": "string", "description": "Path to project"},
                    "token": {"type": "string", "description": "Heroku API key (optional)"}
                },
                "required": ["app_name", "project_path"]
            },
            func=deploy_heroku
        ),
        Tool(
            name="deploy_netlify",
            description="Deploy to Netlify. Requires NETLIFY_AUTH_TOKEN.",
            parameters={
                "type": "object",
                "properties": {
                    "project_path": {"type": "string", "description": "Path to project"},
                    "site_name": {"type": "string", "description": "Site name"},
                    "token": {"type": "string", "description": "Netlify token (optional)"}
                },
                "required": ["project_path"]
            },
            func=deploy_netlify
        ),
        Tool(
            name="deploy_github_pages",
            description="Deploy to GitHub Pages. Requires GITHUB_TOKEN.",
            parameters={
                "type": "object",
                "properties": {
                    "owner": {"type": "string", "description": "GitHub owner"},
                    "repo": {"type": "string", "description": "Repository name"},
                    "project_path": {"type": "string", "description": "Path to project"},
                    "branch": {"type": "string", "description": "Branch", "default": "gh-pages"},
                    "token": {"type": "string", "description": "GitHub token (optional)"}
                },
                "required": ["owner", "repo", "project_path"]
            },
            func=deploy_github_pages
        ),
        Tool(
            name="deploy_docker",
            description="Build and deploy Docker image.",
            parameters={
                "type": "object",
                "properties": {
                    "image_name": {"type": "string", "description": "Image name"},
                    "dockerfile_path": {"type": "string", "description": "Dockerfile path"},
                    "registry": {"type": "string", "description": "Registry URL"}
                },
                "required": ["image_name"]
            },
            func=deploy_docker
        ),

        # Backend Development
        Tool(
            name="backend_create",
            description="Create a complete backend project (Express.js or FastAPI) with API routes, CORS, and health checks.",
            parameters={
                "type": "object",
                "properties": {
                    "project_path": {"type": "string", "description": "Directory path for the project"},
                    "framework": {"type": "string", "description": "Framework: express or fastapi", "default": "express"},
                    "language": {"type": "string", "description": "Language: javascript or python", "default": "javascript"},
                    "port": {"type": "integer", "description": "Server port", "default": 3000},
                    "features": {"type": "array", "items": {"type": "string"}, "description": "Features: api, cors, auth, db", "default": ["api", "cors"]}
                },
                "required": ["project_path"]
            },
            func=backend_create
        ),
        Tool(
            name="backend_start",
            description="Start a backend server process. Auto-installs dependencies if needed.",
            parameters={
                "type": "object",
                "properties": {
                    "project_path": {"type": "string", "description": "Path to backend project"},
                    "command": {"type": "string", "description": "Start command (auto-detected if not specified)"},
                    "port": {"type": "integer", "description": "Port to run on"},
                    "framework": {"type": "string", "description": "express or fastapi"},
                    "env_vars": {"type": "object", "description": "Environment variables"}
                },
                "required": ["project_path"]
            },
            func=backend_start
        ),
        Tool(
            name="backend_stop",
            description="Stop a running backend server.",
            parameters={
                "type": "object",
                "properties": {
                    "project_name": {"type": "string", "description": "Project name to stop"},
                    "pid": {"type": "integer", "description": "Process ID to stop"}
                },
                "required": []
            },
            func=backend_stop
        ),
        Tool(
            name="backend_status",
            description="Check status of running backend servers.",
            parameters={
                "type": "object",
                "properties": {
                    "project_name": {"type": "string", "description": "Specific project to check (optional)"}
                },
                "required": []
            },
            func=backend_status
        ),
        Tool(
            name="backend_test",
            description="Test a backend endpoint (GET or POST).",
            parameters={
                "type": "object",
                "properties": {
                    "endpoint": {"type": "string", "description": "Full URL to test"},
                    "method": {"type": "string", "description": "HTTP method", "default": "GET"},
                    "data": {"type": "object", "description": "JSON body for POST"},
                    "headers": {"type": "object", "description": "Request headers"},
                    "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 10}
                },
                "required": ["endpoint"]
            },
            func=backend_test
        ),
        Tool(
            name="backend_add_route",
            description="Add a new API route to an existing backend project.",
            parameters={
                "type": "object",
                "properties": {
                    "project_path": {"type": "string", "description": "Path to backend project"},
                    "route": {"type": "string", "description": "Route path (e.g., /api/items)"},
                    "method": {"type": "string", "description": "HTTP method", "default": "GET"},
                    "handler_code": {"type": "string", "description": "Custom handler code (optional)"},
                    "framework": {"type": "string", "description": "express or fastapi", "default": "express"}
                },
                "required": ["project_path", "route"]
            },
            func=backend_add_route
        ),

    ]
