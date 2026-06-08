import os
import json
import subprocess
from typing import Dict, List, Any, Optional
import aiohttp

async def deploy_vercel(project_path: str, name: str = None, token: str = None) -> Dict:
    """Deploy to Vercel."""
    try:
        token = token or os.getenv("VERCEL_TOKEN", "")
        if not token:
            return {"error": "Vercel token required. Set VERCEL_TOKEN environment variable."}

        # Check if vercel CLI is available
        check = subprocess.run(["which", "vercel"], capture_output=True, text=True)
        if check.returncode != 0:
            return {"error": "Vercel CLI not found. Install with: npm i -g vercel"}

        env = os.environ.copy()
        env["VERCEL_TOKEN"] = token

        cmd = ["vercel", "--yes", "--token", token]
        if name:
            cmd.extend(["--name", name])

        result = subprocess.run(
            cmd,
            cwd=project_path,
            capture_output=True,
            text=True,
            env=env,
            timeout=120
        )

        return {
            "platform": "vercel",
            "stdout": result.stdout[:5000],
            "stderr": result.stderr[:5000],
            "success": result.returncode == 0,
            "url": extract_url(result.stdout) if result.returncode == 0 else None
        }
    except Exception as e:
        return {"error": str(e)}

async def deploy_heroku(app_name: str, project_path: str, token: str = None) -> Dict:
    """Deploy to Heroku."""
    try:
        token = token or os.getenv("HEROKU_API_KEY", "")
        if not token:
            return {"error": "Heroku API key required. Set HEROKU_API_KEY environment variable."}

        # Login via API key
        env = os.environ.copy()
        env["HEROKU_API_KEY"] = token

        # Check if heroku CLI is available
        check = subprocess.run(["which", "heroku"], capture_output=True, text=True)
        if check.returncode != 0:
            return {"error": "Heroku CLI not found. Install with: npm i -g heroku"}

        # Create app if doesn't exist
        create_result = subprocess.run(
            ["heroku", "apps:create", app_name],
            cwd=project_path,
            capture_output=True,
            text=True,
            env=env
        )

        # Deploy
        result = subprocess.run(
            ["git", "push", "heroku", "main"],
            cwd=project_path,
            capture_output=True,
            text=True,
            env=env,
            timeout=300
        )

        return {
            "platform": "heroku",
            "app_name": app_name,
            "url": f"https://{app_name}.herokuapp.com",
            "stdout": result.stdout[:5000],
            "stderr": result.stderr[:5000],
            "success": result.returncode == 0
        }
    except Exception as e:
        return {"error": str(e)}

async def deploy_netlify(project_path: str, site_name: str = None, token: str = None) -> Dict:
    """Deploy to Netlify."""
    try:
        token = token or os.getenv("NETLIFY_AUTH_TOKEN", "")
        if not token:
            return {"error": "Netlify token required. Set NETLIFY_AUTH_TOKEN environment variable."}

        check = subprocess.run(["which", "netlify"], capture_output=True, text=True)
        if check.returncode != 0:
            return {"error": "Netlify CLI not found. Install with: npm i -g netlify-cli"}

        env = os.environ.copy()
        env["NETLIFY_AUTH_TOKEN"] = token

        cmd = ["netlify", "deploy", "--prod", "--dir", project_path]
        if site_name:
            cmd.extend(["--site", site_name])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            timeout=120
        )

        return {
            "platform": "netlify",
            "stdout": result.stdout[:5000],
            "stderr": result.stderr[:5000],
            "success": result.returncode == 0,
            "url": extract_url(result.stdout) if result.returncode == 0 else None
        }
    except Exception as e:
        return {"error": str(e)}

async def deploy_github_pages(owner: str, repo: str, project_path: str, branch: str = "gh-pages", token: str = None) -> Dict:
    """Deploy to GitHub Pages."""
    try:
        token = token or os.getenv("GITHUB_TOKEN", "")
        if not token:
            return {"error": "GitHub token required. Set GITHUB_TOKEN environment variable."}

        # Use git subtree or gh-pages package
        # For simplicity, push to gh-pages branch
        env = os.environ.copy()
        env["GITHUB_TOKEN"] = token

        # Initialize git if needed
        git_check = subprocess.run(["git", "rev-parse", "--git-dir"], cwd=project_path, capture_output=True, text=True)
        if git_check.returncode != 0:
            subprocess.run(["git", "init"], cwd=project_path, capture_output=True)

        # Create and push to gh-pages branch
        subprocess.run(["git", "checkout", "-b", branch], cwd=project_path, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=project_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Deploy to GitHub Pages"], cwd=project_path, capture_output=True)

        # Push using token
        remote_url = f"https://{token}@github.com/{owner}/{repo}.git"
        result = subprocess.run(
            ["git", "push", "-f", remote_url, branch],
            cwd=project_path,
            capture_output=True,
            text=True,
            env=env,
            timeout=120
        )

        return {
            "platform": "github_pages",
            "url": f"https://{owner}.github.io/{repo}",
            "branch": branch,
            "stdout": result.stdout[:5000],
            "stderr": result.stderr[:5000],
            "success": result.returncode == 0
        }
    except Exception as e:
        return {"error": str(e)}

async def deploy_docker(image_name: str, dockerfile_path: str = None, registry: str = None) -> Dict:
    """Build and deploy Docker image."""
    try:
        # Build image
        build_cmd = ["docker", "build", "-t", image_name, "."]
        if dockerfile_path:
            build_cmd = ["docker", "build", "-f", dockerfile_path, "-t", image_name, "."]

        build_result = subprocess.run(
            build_cmd,
            capture_output=True,
            text=True,
            timeout=300
        )

        if build_result.returncode != 0:
            return {
                "platform": "docker",
                "error": "Build failed",
                "stderr": build_result.stderr[:5000]
            }

        # Push to registry if specified
        if registry:
            tag_cmd = ["docker", "tag", image_name, f"{registry}/{image_name}"]
            subprocess.run(tag_cmd, capture_output=True)

            push_result = subprocess.run(
                ["docker", "push", f"{registry}/{image_name}"],
                capture_output=True,
                text=True,
                timeout=300
            )

            return {
                "platform": "docker",
                "image": f"{registry}/{image_name}",
                "build_success": True,
                "push_success": push_result.returncode == 0,
                "stdout": push_result.stdout[:3000]
            }

        return {
            "platform": "docker",
            "image": image_name,
            "build_success": True
        }
    except Exception as e:
        return {"error": str(e)}

def extract_url(text: str) -> str:
    """Extract URL from deployment output."""
    import re
    urls = re.findall(r'https?://[^\s\)]+', text)
    return urls[0] if urls else None
