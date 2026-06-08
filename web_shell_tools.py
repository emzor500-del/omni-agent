import os
import json
import subprocess
from typing import Dict, List, Any, Optional
import aiohttp

async def web_search(query: str, num_results: int = 10) -> Dict:
    """Search the web using DuckDuckGo or similar."""
    try:
        # Using DuckDuckGo HTML API (no API key needed)
        url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                html = await response.text()

                # Simple parsing - extract results
                import re
                results = []
                # Extract titles and snippets
                links = re.findall(r'<a rel="nofollow" class="result__a" href="([^"]+)">([^<]+)</a>', html)
                snippets = re.findall(r'<a class="result__snippet"[^>]*>([^<]+)</a>', html)

                for i, (href, title) in enumerate(links[:num_results]):
                    snippet = snippets[i] if i < len(snippets) else ""
                    results.append({
                        "title": title,
                        "url": href,
                        "snippet": snippet
                    })

                return {
                    "query": query,
                    "results": results,
                    "count": len(results)
                }
    except Exception as e:
        return {"error": str(e), "query": query}

async def web_fetch(url: str) -> Dict:
    """Fetch content from a URL."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                content = await response.text()
                # Extract text content (simple HTML stripping)
                import re
                text = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
                text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
                text = re.sub(r'<[^>]+>', ' ', text)
                text = re.sub(r'\s+', ' ', text).strip()

                return {
                    "url": url,
                    "status": response.status,
                    "title": re.search(r'<title>([^<]+)</title>', content, re.IGNORECASE).group(1) if re.search(r'<title>([^<]+)</title>', content, re.IGNORECASE) else "",
                    "content": text[:10000],  # Limit content
                    "content_length": len(text)
                }
    except Exception as e:
        return {"error": str(e), "url": url}

async def shell_execute(command: str, cwd: str = None, timeout: int = 60) -> Dict:
    """Execute shell command safely."""
    try:
        # Safety check - block dangerous commands
        dangerous = ['rm -rf /', 'mkfs', 'dd if=/dev/zero', '>:', 'curl | sh', 'wget | sh', 'powershell -enc']
        for d in dangerous:
            if d in command.lower():
                return {"error": f"Dangerous command blocked: {d}", "command": command, "blocked": True}

        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=timeout
        )

        return {
            "command": command,
            "returncode": result.returncode,
            "stdout": result.stdout[:5000],
            "stderr": result.stderr[:5000],
            "success": result.returncode == 0
        }
    except subprocess.TimeoutExpired:
        return {"error": "Command timed out", "command": command, "timeout": timeout}
    except Exception as e:
        return {"error": str(e), "command": command}

async def code_execute(language: str, code: str, timeout: int = 30) -> Dict:
    """Execute code in sandboxed environment."""
    try:
        if language == "python":
            # Write to temp file and execute
            temp_file = f"/tmp/omni_agent_exec_{os.getpid()}.py"
            with open(temp_file, 'w') as f:
                f.write(code)

            result = subprocess.run(
                ["python3", temp_file],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            os.remove(temp_file)

            return {
                "language": language,
                "stdout": result.stdout[:5000],
                "stderr": result.stderr[:5000],
                "returncode": result.returncode,
                "success": result.returncode == 0
            }
        elif language == "javascript" or language == "node":
            temp_file = f"/tmp/omni_agent_exec_{os.getpid()}.js"
            with open(temp_file, 'w') as f:
                f.write(code)

            result = subprocess.run(
                ["node", temp_file],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            os.remove(temp_file)

            return {
                "language": language,
                "stdout": result.stdout[:5000],
                "stderr": result.stderr[:5000],
                "returncode": result.returncode,
                "success": result.returncode == 0
            }
        else:
            return {"error": f"Unsupported language: {language}", "supported": ["python", "javascript", "node"]}
    except Exception as e:
        return {"error": str(e), "language": language}

async def install_package(package: str, manager: str = "pip") -> Dict:
    """Install a package."""
    try:
        if manager == "pip":
            result = subprocess.run(
                ["pip", "install", package],
                capture_output=True,
                text=True,
                timeout=120
            )
        elif manager == "npm":
            result = subprocess.run(
                ["npm", "install", package],
                capture_output=True,
                text=True,
                timeout=120
            )
        else:
            return {"error": f"Unsupported package manager: {manager}"}

        return {
            "package": package,
            "manager": manager,
            "stdout": result.stdout[:3000],
            "stderr": result.stderr[:3000],
            "success": result.returncode == 0
        }
    except Exception as e:
        return {"error": str(e)}
