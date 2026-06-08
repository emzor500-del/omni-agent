import os
import sys
import asyncio
import json
import subprocess
import base64
import glob
import shutil
import time
import signal
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field

import streamlit as st

# ============================================================
# CORE AGENT FRAMEWORK
# ============================================================

@dataclass
class Task:
    id: str
    description: str
    status: str = "pending"
    result: Any = None
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    tool_calls: List[Dict] = field(default_factory=list)

class Tool:
    def __init__(self, name: str, description: str, parameters: Dict, func: Callable):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.func = func

    async def execute(self, **kwargs) -> Any:
        try:
            if asyncio.iscoroutinefunction(self.func):
                return await self.func(**kwargs)
            return self.func(**kwargs)
        except Exception as e:
            import traceback
            return {"error": str(e), "traceback": traceback.format_exc()}

class LLMClient:
    def __init__(self, provider: str = "openai", api_key: str = None, model: str = None):
        self.provider = provider.lower()
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model or "gpt-4o"
        self.base_url = "https://api.openai.com/v1"

    async def chat_completion(self, messages: List[Dict], tools: List[Dict] = None, tool_choice: str = "auto") -> Dict:
        import aiohttp
        payload = {
            "model": self.model,
            "messages": messages,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = tool_choice

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}/chat/completions", headers=headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API Error {response.status}: {error_text}")
                return await response.json()

class OmniAgent:
    def __init__(self, llm_client, config: Dict = None):
        self.llm = llm_client
        self.config = config or {}
        self.tools: Dict[str, Tool] = {}
        self.tasks: Dict[str, Task] = {}
        self.memory: List[Dict] = []
        self.max_iterations = self.config.get("max_iterations", 50)
        self.auto_approve = self.config.get("auto_approve", True)

    def register_tool(self, tool: Tool):
        self.tools[tool.name] = tool

    def get_tool_schema(self) -> List[Dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
            }
            for tool in self.tools.values()
        ]

    async def execute_task(self, task_id: str, description: str, context: Dict = None) -> Task:
        task = Task(id=task_id, description=description)
        self.tasks[task_id] = task
        task.status = "running"

        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": description}
        ]

        if context:
            messages.insert(1, {"role": "system", "content": f"Context: {json.dumps(context, indent=2)}"})

        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1

            try:
                response = await self.llm.chat_completion(
                    messages=messages,
                    tools=self.get_tool_schema(),
                    tool_choice="auto"
                )

                message = response.get("choices", [{}])[0].get("message", {})
                messages.append(message)

                tool_calls = message.get("tool_calls", [])

                if not tool_calls:
                    task.result = message.get("content", "Task completed")
                    task.status = "completed"
                    task.completed_at = datetime.now().isoformat()
                    return task

                for tool_call in tool_calls:
                    tool_name = tool_call["function"]["name"]
                    tool_args = json.loads(tool_call["function"]["arguments"])

                    if tool_name in self.tools:
                        result = await self.tools[tool_name].execute(**tool_args)
                        task.tool_calls.append({"tool": tool_name, "args": tool_args, "result": result})
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "content": json.dumps(result, default=str)[:10000]
                        })
                    else:
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "content": f"Error: Tool '{tool_name}' not found."
                        })

            except Exception as e:
                task.error = str(e)
                task.status = "failed"
                task.completed_at = datetime.now().isoformat()
                return task

        task.status = "failed"
        task.error = "Max iterations reached"
        task.completed_at = datetime.now().isoformat()
        return task

    def _get_system_prompt(self) -> str:
        return """You are OmniAgent, a powerful autonomous AI agent. Use the available tools to complete tasks. Be thorough and efficient."""

# ============================================================
# TOOL IMPLEMENTATIONS
# ============================================================

async def file_read(path: str, offset: int = 0, limit: int = 1000) -> Dict:
    try:
        if not os.path.exists(path):
            return {"error": f"File not found: {path}"}
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            if offset > 0:
                for _ in range(offset): f.readline()
            lines = [f.readline().rstrip('\n') for _ in range(limit) if f.readline()]
        return {"path": path, "content": '\n'.join(lines), "success": True}
    except Exception as e:
        return {"error": str(e)}

async def file_write(path: str, content: str, append: bool = False) -> Dict:
    try:
        os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
        with open(path, 'a' if append else 'w', encoding='utf-8') as f:
            f.write(content)
        return {"path": path, "bytes_written": len(content.encode('utf-8')), "success": True}
    except Exception as e:
        return {"error": str(e)}

async def file_list(directory: str = ".", pattern: str = "*", recursive: bool = False) -> Dict:
    try:
        files = glob.glob(os.path.join(directory, "**" if recursive else "", pattern), recursive=recursive)
        files = [f for f in files if os.path.isfile(f)]
        return {"directory": directory, "files": files[:100], "count": len(files)}
    except Exception as e:
        return {"error": str(e)}

async def shell_execute(command: str, cwd: str = None, timeout: int = 60) -> Dict:
    try:
        dangerous = ['rm -rf /', 'mkfs', 'dd if=/dev/zero', '>:', 'curl | sh', 'wget | sh']
        for d in dangerous:
            if d in command.lower():
                return {"error": f"Dangerous command blocked: {d}", "blocked": True}
        result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=cwd, timeout=timeout)
        return {"command": command, "returncode": result.returncode, "stdout": result.stdout[:5000], "stderr": result.stderr[:5000], "success": result.returncode == 0}
    except Exception as e:
        return {"error": str(e)}

async def web_search(query: str, num_results: int = 10) -> Dict:
    try:
        import urllib.request
        import urllib.parse
        import re
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8')
        links = re.findall(r'<a rel="nofollow" class="result__a" href="([^"]+)">([^<]+)</a>', html)
        results = [{"title": title, "url": href} for href, title in links[:num_results]]
        return {"query": query, "results": results, "count": len(results)}
    except Exception as e:
        return {"error": str(e)}

async def github_create_repo(name: str, description: str = "", private: bool = False) -> Dict:
    try:
        import urllib.request
        token = os.getenv("GITHUB_TOKEN", "")
        data = json.dumps({"name": name, "description": description, "private": private}).encode()
        req = urllib.request.Request(
            "https://api.github.com/user/repos",
            data=data,
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json"
            }
        )
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        return {"error": str(e)}

async def github_create_file(owner: str, repo: str, path: str, content: str, message: str = "Update via OmniAgent", branch: str = "main") -> Dict:
    try:
        import urllib.request
        token = os.getenv("GITHUB_TOKEN", "")
        encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        data = json.dumps({"message": message, "content": encoded, "branch": branch}).encode()
        req = urllib.request.Request(
            f"https://api.github.com/repos/{owner}/{repo}/contents/{path}",
            data=data,
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json"
            }
        )
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        return {"error": str(e)}

async def backend_create(project_path: str, framework: str = "express", port: int = 3000) -> Dict:
    try:
        os.makedirs(project_path, exist_ok=True)
        if framework == "express":
            pkg = {"name": os.path.basename(project_path), "version": "1.0.0", "main": "server.js",
                   "scripts": {"start": "node server.js"}, "dependencies": {"express": "^4.18.2", "cors": "^2.8.5"}}
            with open(os.path.join(project_path, "package.json"), "w") as f:
                json.dump(pkg, f, indent=2)
            server = """const express = require('express');\nconst app = express();\nconst PORT = process.env.PORT || 3000;\napp.use(require('cors')());\napp.use(express.json());\napp.get('/health', (req, res) => res.json({status: 'ok'}));\napp.get('/api', (req, res) => res.json({message: 'API running'}));\napp.listen(PORT, () => console.log(`Server on port ${PORT}`));\n"""
            with open(os.path.join(project_path, "server.js"), "w") as f:
                f.write(server)
            return {"framework": "express", "files": ["package.json", "server.js"], "success": True}
        elif framework == "fastapi":
            req = "fastapi\nuvicorn\n"
            with open(os.path.join(project_path, "requirements.txt"), "w") as f:
                f.write(req)
            main = """from fastapi import FastAPI\napp = FastAPI()\n@app.get('/health')\nasync def health():\n    return {'status': 'ok'}\n@app.get('/api')\nasync def api():\n    return {'message': 'API running'}\nif __name__ == '__main__':\n    import uvicorn\n    uvicorn.run(app, host='0.0.0.0', port=8000)\n"""
            with open(os.path.join(project_path, "main.py"), "w") as f:
                f.write(main)
            return {"framework": "fastapi", "files": ["requirements.txt", "main.py"], "success": True}
        return {"error": "Unsupported framework"}
    except Exception as e:
        return {"error": str(e)}

async def code_execute(language: str, code: str, timeout: int = 30) -> Dict:
    try:
        if language == "python":
            temp = f"/tmp/omni_exec_{os.getpid()}.py"
            with open(temp, 'w') as f:
                f.write(code)
            result = subprocess.run(["python3", temp], capture_output=True, text=True, timeout=timeout)
            os.remove(temp)
            return {"stdout": result.stdout[:5000], "stderr": result.stderr[:5000], "success": result.returncode == 0}
        return {"error": "Unsupported language"}
    except Exception as e:
        return {"error": str(e)}

async def install_package(package: str, manager: str = "pip") -> Dict:
    try:
        cmd = ["pip", "install", package] if manager == "pip" else ["npm", "install", package]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return {"success": result.returncode == 0, "stdout": result.stdout[:3000]}
    except Exception as e:
        return {"error": str(e)}

# ============================================================
# TOOL REGISTRY
# ============================================================

def get_all_tools():
    return [
        Tool(name="file_read", description="Read a file", parameters={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}, func=file_read),
        Tool(name="file_write", description="Write to a file", parameters={"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}, func=file_write),
        Tool(name="file_list", description="List files", parameters={"type": "object", "properties": {"directory": {"type": "string", "default": "."}}, "required": []}, func=file_list),
        Tool(name="shell_execute", description="Run shell commands", parameters={"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}, func=shell_execute),
        Tool(name="web_search", description="Search the web", parameters={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}, func=web_search),
        Tool(name="github_create_repo", description="Create GitHub repo", parameters={"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}, func=github_create_repo),
        Tool(name="github_create_file", description="Create file in GitHub repo", parameters={"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "path": {"type": "string"}, "content": {"type": "string"}}, "required": ["owner", "repo", "path", "content"]}, func=github_create_file),
        Tool(name="backend_create", description="Create a backend project", parameters={"type": "object", "properties": {"project_path": {"type": "string"}, "framework": {"type": "string", "default": "express"}}, "required": ["project_path"]}, func=backend_create),
        Tool(name="code_execute", description="Execute Python code", parameters={"type": "object", "properties": {"language": {"type": "string"}, "code": {"type": "string"}}, "required": ["language", "code"]}, func=code_execute),
        Tool(name="install_package", description="Install a package", parameters={"type": "object", "properties": {"package": {"type": "string"}}, "required": ["package"]}, func=install_package),
    ]

# ============================================================
# STREAMLIT UI
# ============================================================

st.set_page_config(page_title="OmniAgent", page_icon="🤖", layout="wide")

st.markdown("""
<style>
.main-header { font-size: 2.5rem; font-weight: bold; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; }
.task-card { background: #1e1e1e; border-radius: 10px; padding: 1rem; margin: 0.5rem 0; border-left: 4px solid #667eea; }
.status-completed { color: #4ade80; } .status-failed { color: #f87171; }
.chat-message { padding: 1rem; border-radius: 10px; margin: 0.5rem 0; }
.user-message { background: #1e3a5f; margin-left: 1rem; }
.agent-message { background: #1e1e2e; margin-right: 1rem; border-left: 3px solid #667eea; }
</style>
""", unsafe_allow_html=True)

if "agent" not in st.session_state:
    api_key = os.getenv("OPENAI_API_KEY", "")
    llm = LLMClient(api_key=api_key)
    agent = OmniAgent(llm, config={"auto_approve": True, "max_iterations": 30})
    for tool in get_all_tools():
        agent.register_tool(tool)
    st.session_state.agent = agent
    st.session_state.tasks = []
    st.session_state.chat_history = []
    st.session_state.running = False

agent = st.session_state.agent

st.markdown('<div class="main-header">🤖 OmniAgent</div>', unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888;'>Autonomous AI Agent — Code, Deploy, GitHub, Backend</p>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## ⚙️ Settings")
    api_key = st.text_input("OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
        agent.llm.api_key = api_key

    github_token = st.text_input("GitHub Token", type="password", value=os.getenv("GITHUB_TOKEN", ""))
    if github_token:
        os.environ["GITHUB_TOKEN"] = github_token

    st.markdown("---")
    st.markdown("### 📊 Stats")
    st.metric("Tasks", len([t for t in st.session_state.tasks if t.status == "completed"]))
    st.metric("Tools", len(agent.tools))

    st.markdown("---")
    st.markdown("### 💡 Quick Tasks")
    quick_tasks = {
        "📝 Hello World": "Create a Python hello world script",
        "🌐 Web Scraper": "Create a web scraper for news headlines",
        "🗄️ Express API": "Create an Express.js backend",
        "🐍 FastAPI": "Create a FastAPI backend",
        "🔍 Search": "Search for latest AI news",
    }
    for label, task in quick_tasks.items():
        if st.button(label, use_container_width=True):
            st.session_state.quick_task = task
            st.rerun()

    if st.button("🗑️ Clear", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.tasks = []
        st.rerun()

st.markdown("---")

for msg in st.session_state.chat_history:
    if msg["role"] == "user":
        st.markdown(f'<div class="chat-message user-message"><strong>👤 You:</strong><br>{msg["content"].replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chat-message agent-message"><strong>🤖 Agent:</strong><br>{msg["content"].replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)

with st.container():
    if "quick_task" in st.session_state:
        user_input = st.session_state.quick_task
        del st.session_state.quick_task
        execute = True
    else:
        col1, col2 = st.columns([5, 1])
        with col1:
            user_input = st.text_area("What do you want to build?", placeholder="Create an Express API and push to GitHub...", height=100, key="user_input", label_visibility="collapsed")
        with col2:
            st.write("")
            st.write("")
            execute = st.button("🚀 Run", use_container_width=True, type="primary")

    if execute and user_input.strip() and not st.session_state.running:
        st.session_state.running = True
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        async def run_task():
            return await agent.execute_task(task_id, user_input)

        try:
            with st.spinner("🤖 Working..."):
                task = asyncio.run(run_task())
            st.session_state.tasks.append(task)
            response = task.result if task.status == "completed" else f"❌ Failed: {task.error}"
            st.session_state.chat_history.append({"role": "agent", "content": response})
            if task.tool_calls:
                with st.expander(f"🔧 Tools ({len(task.tool_calls)})", expanded=False):
                    for i, tc in enumerate(task.tool_calls, 1):
                        icon = "✅" if "error" not in str(tc.get("result", "")).lower() else "❌"
                        st.markdown(f"**{i}. {icon} `{tc['tool']}`**")
                        st.json(tc['args'])
        except Exception as e:
            st.error(f"Error: {e}")
        finally:
            st.session_state.running = False
            st.rerun()

if st.session_state.tasks:
    st.markdown("---")
    st.markdown("### 📚 Recent Tasks")
    for task in reversed(st.session_state.tasks[-5:]):
        color = {"completed": "#4ade80", "failed": "#f87171"}.get(task.status, "#888")
        st.markdown(f'<div class="task-card"><span style="color: {color}">● {task.status.upper()}</span> | <small>{task.description[:80]}...</small></div>', unsafe_allow_html=True)

st.markdown("---")
st.markdown("<p style='text-align: center; color: #666; font-size: 0.8rem;'>OmniAgent v1.1 | 10 Tools | Cloud-Ready</p>", unsafe_allow_html=True)
