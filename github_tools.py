import os
import base64
import json
from typing import Dict, List, Any, Optional
import aiohttp

class GitHubClient:
    def __init__(self, token: str = None):
        self.token = token or os.getenv("GITHUB_TOKEN", "")
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "OmniAgent/1.0"
        }

    async def _request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        url = f"{self.base_url}{endpoint}"
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, headers=self.headers, json=data) as response:
                result = await response.json()
                if response.status >= 400:
                    return {"error": result.get("message", f"HTTP {response.status}"), "status": response.status}
                return result

    async def create_repo(self, name: str, description: str = "", private: bool = False, auto_init: bool = True) -> Dict:
        """Create a new GitHub repository."""
        data = {
            "name": name,
            "description": description,
            "private": private,
            "auto_init": auto_init
        }
        return await self._request("POST", "/user/repos", data)

    async def list_repos(self) -> Dict:
        """List user's repositories."""
        return await self._request("GET", "/user/repos")

    async def get_repo(self, owner: str, repo: str) -> Dict:
        """Get repository details."""
        return await self._request("GET", f"/repos/{owner}/{repo}")

    async def create_file(self, owner: str, repo: str, path: str, content: str, message: str = "Add file via OmniAgent", branch: str = "main") -> Dict:
        """Create or update a file in a repository."""
        encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        data = {
            "message": message,
            "content": encoded_content,
            "branch": branch
        }
        return await self._request("PUT", f"/repos/{owner}/{repo}/contents/{path}", data)

    async def get_file(self, owner: str, repo: str, path: str, branch: str = "main") -> Dict:
        """Get file contents from repository."""
        result = await self._request("GET", f"/repos/{owner}/{repo}/contents/{path}?ref={branch}")
        if "content" in result:
            result["decoded_content"] = base64.b64decode(result["content"]).decode('utf-8')
        return result

    async def delete_file(self, owner: str, repo: str, path: str, sha: str, message: str = "Delete file via OmniAgent", branch: str = "main") -> Dict:
        """Delete a file from repository."""
        data = {
            "message": message,
            "sha": sha,
            "branch": branch
        }
        return await self._request("DELETE", f"/repos/{owner}/{repo}/contents/{path}", data)

    async def list_files(self, owner: str, repo: str, path: str = "", branch: str = "main") -> Dict:
        """List files in repository directory."""
        return await self._request("GET", f"/repos/{owner}/{repo}/contents/{path}?ref={branch}")

    async def create_branch(self, owner: str, repo: str, branch: str, from_branch: str = "main") -> Dict:
        """Create a new branch."""
        # Get SHA of from_branch
        ref_result = await self._request("GET", f"/repos/{owner}/{repo}/git/refs/heads/{from_branch}")
        if "error" in ref_result:
            return ref_result

        sha = ref_result.get("object", {}).get("sha")
        data = {
            "ref": f"refs/heads/{branch}",
            "sha": sha
        }
        return await self._request("POST", f"/repos/{owner}/{repo}/git/refs", data)

    async def create_pull_request(self, owner: str, repo: str, title: str, head: str, base: str, body: str = "") -> Dict:
        """Create a pull request."""
        data = {
            "title": title,
            "head": head,
            "base": base,
            "body": body
        }
        return await self._request("POST", f"/repos/{owner}/{repo}/pulls", data)

    async def create_issue(self, owner: str, repo: str, title: str, body: str = "", labels: List[str] = None) -> Dict:
        """Create an issue."""
        data = {
            "title": title,
            "body": body
        }
        if labels:
            data["labels"] = labels
        return await self._request("POST", f"/repos/{owner}/{repo}/issues", data)

    async def list_issues(self, owner: str, repo: str, state: str = "open") -> Dict:
        """List repository issues."""
        return await self._request("GET", f"/repos/{owner}/{repo}/issues?state={state}")

    async def get_user(self) -> Dict:
        """Get authenticated user info."""
        return await self._request("GET", "/user")

    async def push_directory(self, owner: str, repo: str, local_path: str, remote_path: str = "", branch: str = "main") -> Dict:
        """Push entire directory to GitHub."""
        import os
        results = []
        for root, _, files in os.walk(local_path):
            for file in files:
                local_file = os.path.join(root, file)
                rel_path = os.path.relpath(local_file, local_path)
                remote_file_path = f"{remote_path}/{rel_path}".replace("\\", "/").strip("/")

                try:
                    with open(local_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    result = await self.create_file(owner, repo, remote_file_path, content, branch=branch)
                    results.append({"file": remote_file_path, "status": "success" if "error" not in result else "error", "detail": result})
                except Exception as e:
                    results.append({"file": remote_file_path, "status": "error", "detail": str(e)})

        return {"pushed": len(results), "results": results}

# Tool wrapper functions for agent integration
async def github_create_repo(name: str, description: str = "", private: bool = False) -> Dict:
    client = GitHubClient()
    return await client.create_repo(name, description, private)

async def github_list_repos() -> Dict:
    client = GitHubClient()
    return await client.list_repos()

async def github_create_file(owner: str, repo: str, path: str, content: str, message: str = "Update via OmniAgent", branch: str = "main") -> Dict:
    client = GitHubClient()
    return await client.create_file(owner, repo, path, content, message, branch)

async def github_get_file(owner: str, repo: str, path: str, branch: str = "main") -> Dict:
    client = GitHubClient()
    return await client.get_file(owner, repo, path, branch)

async def github_list_files(owner: str, repo: str, path: str = "", branch: str = "main") -> Dict:
    client = GitHubClient()
    return await client.list_files(owner, repo, path, branch)

async def github_create_branch(owner: str, repo: str, branch: str, from_branch: str = "main") -> Dict:
    client = GitHubClient()
    return await client.create_branch(owner, repo, branch, from_branch)

async def github_create_pr(owner: str, repo: str, title: str, head: str, base: str, body: str = "") -> Dict:
    client = GitHubClient()
    return await client.create_pull_request(owner, repo, title, head, base, body)

async def github_create_issue(owner: str, repo: str, title: str, body: str = "", labels: List[str] = None) -> Dict:
    client = GitHubClient()
    return await client.create_issue(owner, repo, title, body, labels)

async def github_push_directory(owner: str, repo: str, local_path: str, remote_path: str = "", branch: str = "main") -> Dict:
    client = GitHubClient()
    return await client.push_directory(owner, repo, local_path, remote_path, branch)

async def github_get_user() -> Dict:
    client = GitHubClient()
    return await client.get_user()
