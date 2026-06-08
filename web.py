import os
import sys
import asyncio
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agent import OmniAgent
from core.llm_client import LLMClient
from tools.tool_registry import get_all_tools
from tools.backend_tools import backend_create, backend_start, backend_stop, backend_status, backend_test

import streamlit as st

st.set_page_config(page_title="OmniAgent", page_icon="🤖", layout="wide")

st.markdown("""
<style>
.main-header { font-size: 3rem; font-weight: bold; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; }
.task-card { background: #1e1e1e; border-radius: 10px; padding: 1rem; margin: 0.5rem 0; border-left: 4px solid #667eea; }
.status-completed { color: #4ade80; } .status-failed { color: #f87171; } .status-running { color: #60a5fa; }
.backend-card { background: #1a1a2e; border-radius: 8px; padding: 1rem; margin: 0.5rem 0; border: 1px solid #667eea; }
</style>
""", unsafe_allow_html=True)

if "agent" not in st.session_state:
    llm = LLMClient(provider=os.getenv("OMNI_PROVIDER", "openai"), api_key=os.getenv("OMNI_API_KEY"), model=os.getenv("OMNI_MODEL"))
    agent = OmniAgent(llm, config={"auto_approve": True, "max_iterations": 100})
    for tool in get_all_tools(): agent.register_tool(tool)
    st.session_state.agent = agent
    st.session_state.tasks = []
    st.session_state.chat_history = []
    st.session_state.backends = {}

agent = st.session_state.agent

st.markdown('<div class="main-header">🤖 OmniAgent</div>', unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888;'>Autonomous AI Agent with Backend Dev, GitHub, and Deployment</p>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    provider = st.selectbox("LLM Provider", ["openai", "anthropic", "groq", "ollama"], index=0)
    model = st.text_input("Model", value=os.getenv("OMNI_MODEL", "gpt-4o"))

    st.markdown("---")
    st.markdown("### 🖥️ Backend Quick Actions")

    with st.expander("Create Backend"):
        backend_name = st.text_input("Project Name", "my-api")
        backend_framework = st.selectbox("Framework", ["express", "fastapi"])
        backend_port = st.number_input("Port", 3000, 65535, 3000)
        if st.button("Create Backend"):
            project_path = os.path.join(os.getcwd(), backend_name)
            result = asyncio.run(backend_create(project_path, framework=backend_framework, port=backend_port))
            if result.get("success"):
                st.success(f"Created {backend_framework} backend at {project_path}")
                st.session_state.backends[backend_name] = {"path": project_path, "framework": backend_framework, "port": backend_port, "status": "created"}
            else:
                st.error(result.get("error"))

    with st.expander("Manage Backends"):
        if st.session_state.backends:
            for name, info in list(st.session_state.backends.items()):
                cols = st.columns([2, 1, 1])
                cols[0].write(f"{name} ({info['framework']})")
                if info.get("status") == "running":
                    if cols[1].button("Stop", key=f"stop_{name}"):
                        result = asyncio.run(backend_stop(project_name=name))
                        if result.get("success"):
                            info["status"] = "stopped"
                            st.success("Stopped")
                        else:
                            st.error(result.get("error"))
                else:
                    if cols[1].button("Start", key=f"start_{name}"):
                        result = asyncio.run(backend_start(info["path"], port=info.get("port"), framework=info["framework"]))
                        if result.get("success"):
                            info["status"] = "running"
                            info["pid"] = result.get("pid")
                            st.success(f"Started on port {info.get('port')}")
                        else:
                            st.error(result.get("error"))
                if cols[2].button("Test", key=f"test_{name}"):
                    port = info.get("port", 3000)
                    result = asyncio.run(backend_test(f"http://localhost:{port}/health"))
                    st.json(result)
        else:
            st.write("No backends created yet")

    st.markdown("---")
    st.markdown("### 📊 Stats")
    st.metric("Tasks Completed", len([t for t in st.session_state.tasks if t.status == "completed"]))
    st.metric("Tasks Failed", len([t for t in st.session_state.tasks if t.status == "failed"]))
    st.metric("Tools Available", len(agent.tools))
    st.metric("Backends", len(st.session_state.backends))

st.markdown("---")

# Pipeline examples
with st.expander("💡 Pipeline Examples (click to copy)"):
    examples = [
        "Create an Express API with user auth, start it locally, test the endpoints, create a GitHub repo called my-api, push all code, and deploy to Vercel",
        "Build a FastAPI backend with CRUD operations, test it, create GitHub repo, push code, deploy to Heroku",
        "Create a Node.js REST API, add a /products route, start server, verify it's working, push to GitHub, deploy to Netlify",
        "Build a Python backend with SQLAlchemy, start it, test database endpoints, create repo, push, deploy to Render",
    ]
    for ex in examples:
        st.code(ex, language="text")

# Chat history
for msg in st.session_state.chat_history:
    if msg["role"] == "user":
        st.markdown(f'<div style="background: #1e3a5f; padding: 1rem; border-radius: 10px; margin: 0.5rem 0; margin-left: 2rem;"><strong>You:</strong><br>{msg["content"].replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="background: #1e1e2e; padding: 1rem; border-radius: 10px; margin: 0.5rem 0; margin-right: 2rem; border-left: 3px solid #667eea;"><strong>OmniAgent:</strong><br>{msg["content"].replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)

col1, col2 = st.columns([6, 1])
with col1:
    user_input = st.text_area("Enter your task or pipeline...", 
        placeholder="Examples:\n• Create an Express API, start it, test it, push to GitHub, deploy to Vercel\n• Build a FastAPI backend with auth, create GitHub repo, push, deploy\n• Create a backend, add custom routes, test, then deploy to Heroku",
        height=120, key="user_input")
with col2:
    st.write("")
    st.write("")
    execute_btn = st.button("🚀 Execute", use_container_width=True, type="primary")

if execute_btn and user_input.strip():
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    async def run_task():
        # Detect if this is a pipeline task
        pipeline_keywords = ["create", "build", "backend", "api", "server", "start", "test", "deploy", "push", "github"]
        is_pipeline = sum(1 for kw in pipeline_keywords if kw in user_input.lower()) >= 3

        context = None
        if is_pipeline:
            context = {
                "mode": "pipeline",
                "hint": "This is a multi-step pipeline. Execute tools in sequence: create backend → start → test → GitHub → deploy."
            }

        return await agent.execute_task(task_id, user_input, context=context)

    try:
        with st.spinner("Executing pipeline... (this may take several minutes)"):
            task = asyncio.run(run_task())
        st.session_state.tasks.append(task)

        response = task.result if task.status == "completed" else f"Task failed: {task.error}"
        st.session_state.chat_history.append({"role": "agent", "content": response})

        with st.expander(f"Task Details: {task_id}", expanded=True):
            cols = st.columns(4)
            cols[0].metric("Status", task.status)
            cols[1].metric("Tools Used", len(task.tool_calls))
            cols[2].metric("Iterations", len(task.tool_calls) + 1)
            cols[3].metric("Pipeline", "Yes" if any(kw in user_input.lower() for kw in ["create", "deploy", "github"]) else "No")

            if task.tool_calls:
                st.markdown("### 🔧 Tool Execution Chain")
                for i, tc in enumerate(task.tool_calls, 1):
                    success = "error" not in str(tc.get("result", "")).lower()
                    icon = "✅" if success else "❌"
                    with st.container():
                        st.markdown(f"**{i}. {icon} {tc['tool']}**")
                        st.json(tc['args'])
                        if not success:
                            st.error(str(tc.get("result", ""))[:500])
        st.rerun()
    except Exception as e:
        st.error(f"Error: {e}")
        import traceback
        st.code(traceback.format_exc())

# Task history
if st.session_state.tasks:
    st.markdown("---")
    st.markdown("### 📚 Task History")
    for task in reversed(st.session_state.tasks[-10:]):
        status_color = {"completed": "#4ade80", "failed": "#f87171", "running": "#60a5fa", "pending": "#9ca3af"}.get(task.status, "#888")
        st.markdown(f'<div class="task-card"><strong style="color: {status_color}">● {task.status.upper()}</strong> | {task.id}<br><small>{task.description[:100]}...</small><br><small>Tools: {len(task.tool_calls)} | {task.created_at}</small></div>', unsafe_allow_html=True)

# Running backends display
if st.session_state.backends:
    st.markdown("---")
    st.markdown("### 🖥️ Running Backends")
    for name, info in st.session_state.backends.items():
        status = info.get("status", "unknown")
        color = "#4ade80" if status == "running" else "#9ca3af"
        st.markdown(f'<div class="backend-card"><strong style="color: {color}">● {status.upper()}</strong> | {name} ({info["framework"]})<br><small>Port: {info.get("port", "auto")} | PID: {info.get("pid", "N/A")} | Path: {info["path"]}</small></div>', unsafe_allow_html=True)
