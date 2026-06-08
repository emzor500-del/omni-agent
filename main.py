#!/usr/bin/env python3
"""
OmniAgent - Autonomous AI Agent
================================
A powerful autonomous agent capable of:
- File operations (read, write, search, manage)
- Code generation and execution
- Web search and research
- GitHub integration (repos, commits, PRs, issues)
- Backend development (Express.js, FastAPI)
- Server management (start, stop, test)
- Deployment to Vercel, Heroku, Netlify, GitHub Pages, Docker
- Shell command execution
- Multi-step task automation with full pipeline support

Usage:
    python main.py --cli                    # Run CLI interface
    python main.py --web                    # Run Web UI (Streamlit)
    python main.py --task "..."             # Execute single task
    python main.py --backend my-api         # Create and run backend
    python main.py --pipeline "..."       # Full pipeline mode
"""

import os
import sys
import argparse
import asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.agent import OmniAgent
from core.llm_client import LLMClient
from tools.tool_registry import get_all_tools

def setup_environment():
    """Check and display environment setup."""
    print("=" * 60)
    print("OmniAgent Environment Check")
    print("=" * 60)

    env_vars = {
        "OPENAI_API_KEY": "OpenAI API access",
        "ANTHROPIC_API_KEY": "Anthropic/Claude API access",
        "GROQ_API_KEY": "Groq API access",
        "GITHUB_TOKEN": "GitHub operations",
        "VERCEL_TOKEN": "Vercel deployment",
        "NETLIFY_AUTH_TOKEN": "Netlify deployment",
        "HEROKU_API_KEY": "Heroku deployment",
    }

    for var, description in env_vars.items():
        status = "✅" if os.getenv(var) else "❌"
        print(f"{status} {var:<25} - {description}")

    print("=" * 60)
    print()

async def execute_single_task(task_description: str, provider: str = "openai", model: str = None):
    """Execute a single task and print results."""
    llm = LLMClient(provider=provider, api_key=os.getenv("OMNI_API_KEY"), model=model)
    agent = OmniAgent(llm, config={"auto_approve": True, "max_iterations": 50})

    for tool in get_all_tools():
        agent.register_tool(tool)

    print(f"\n🚀 Executing: {task_description}\n")

    task_id = f"task_{asyncio.get_event_loop().time()}"
    task = await agent.execute_task(task_id, task_description)

    print(f"\n{'='*60}")
    print(f"Status: {task.status.upper()}")
    print(f"{'='*60}")

    if task.status == "completed":
        print(f"\n📋 Result:\n{task.result}")
    else:
        print(f"\n❌ Error: {task.error}")

    if task.tool_calls:
        print(f"\n🔧 Tools used ({len(task.tool_calls)}):")
        for tc in task.tool_calls:
            print(f"  • {tc['tool']}: {tc['args']}")

    return task

async def create_and_run_backend(project_name: str, framework: str = "express", port: int = 3000):
    """Quick backend creation and startup."""
    from tools.backend_tools import backend_create, backend_start, backend_test

    project_path = os.path.join(os.getcwd(), project_name)

    print(f"\n🔧 Creating {framework} backend: {project_name}")
    result = await backend_create(project_path, framework=framework, port=port)

    if "error" in result:
        print(f"❌ Creation failed: {result['error']}")
        return

    print(f"✅ Created at {project_path}")
    print(f"   Files: {', '.join(result['files_created'])}")

    print(f"\n🚀 Starting server on port {port}...")
    start_result = await backend_start(project_path, port=port, framework=framework)

    if "error" in start_result:
        print(f"❌ Start failed: {start_result['error']}")
        return

    print(f"✅ Server running!")
    print(f"   PID: {start_result['pid']}")
    print(f"   URL: http://localhost:{port}")

    # Test it
    await asyncio.sleep(2)
    test_result = await backend_test(f"http://localhost:{port}/health")

    if test_result.get("status") == 200:
        print(f"✅ Health check passed!")
        print(f"   Response: {test_result['body'][:200]}")
    else:
        print(f"⚠️ Health check: {test_result}")

    print(f"\n💡 To push to GitHub, run:")
    print(f"   python main.py --task 'Push {project_name} to GitHub and create a repo'")

async def run_pipeline(task_description: str, provider: str = "openai", model: str = None):
    """Run a full pipeline task with enhanced context."""
    llm = LLMClient(provider=provider, api_key=os.getenv("OMNI_API_KEY"), model=model)

    # Enhanced config for pipeline mode - more iterations, auto-approve
    agent = OmniAgent(llm, config={
        "auto_approve": True, 
        "max_iterations": 100  # More iterations for complex pipelines
    })

    for tool in get_all_tools():
        agent.register_tool(tool)

    print(f"\n🚀 PIPELINE MODE: {task_description}\n")
    print("This mode allows the agent to execute multi-step workflows automatically.")
    print("The agent will: create code → test locally → push to GitHub → deploy\n")

    task_id = f"pipeline_{asyncio.get_event_loop().time()}"

    # Add pipeline context to help the agent understand the full workflow
    context = {
        "mode": "pipeline",
        "capabilities": [
            "Create backend projects with backend_create",
            "Start servers with backend_start",
            "Test endpoints with backend_test",
            "Create GitHub repos with github_create_repo",
            "Push files with github_create_file or github_push_directory",
            "Deploy with deploy_vercel, deploy_heroku, deploy_netlify, deploy_github_pages",
            "Execute shell commands with shell_execute",
            "Install packages with install_package"
        ],
        "workflow": "1. Create project locally → 2. Start and test → 3. Create GitHub repo → 4. Push code → 5. Deploy"
    }

    task = await agent.execute_task(task_id, task_description, context=context)

    print(f"\n{'='*60}")
    print(f"Pipeline Status: {task.status.upper()}")
    print(f"{'='*60}")

    if task.status == "completed":
        print(f"\n📋 Result:\n{task.result}")
    else:
        print(f"\n❌ Error: {task.error}")

    if task.tool_calls:
        print(f"\n🔧 Tools used ({len(task.tool_calls)}):")
        for i, tc in enumerate(task.tool_calls, 1):
            status = "✅" if "error" not in str(tc.get("result", "")) else "❌"
            print(f"  {i}. {status} {tc['tool']}")
            print(f"     Args: {tc['args']}")

    return task

def main():
    parser = argparse.ArgumentParser(description="OmniAgent - Autonomous AI Agent")
    parser.add_argument("--cli", action="store_true", help="Run CLI interface")
    parser.add_argument("--web", action="store_true", help="Run Web UI")
    parser.add_argument("--task", type=str, help="Execute single task")
    parser.add_argument("--pipeline", type=str, help="Execute full pipeline (create → test → push → deploy)")
    parser.add_argument("--backend", type=str, help="Quick backend creation (project name)")
    parser.add_argument("--framework", type=str, default="express", help="Backend framework: express or fastapi")
    parser.add_argument("--port", type=int, default=3000, help="Backend port")
    parser.add_argument("--provider", type=str, default="openai", help="LLM provider")
    parser.add_argument("--model", type=str, help="Model name")
    parser.add_argument("--check", action="store_true", help="Check environment")

    args = parser.parse_args()

    if args.check or not (args.cli or args.web or args.task or args.backend or args.pipeline):
        setup_environment()

        if not (args.cli or args.web or args.task or args.backend or args.pipeline):
            print("Usage:")
            print("  python main.py --cli                    # Interactive CLI")
            print("  python main.py --web                    # Web UI (streamlit)")
            print("  python main.py --task '...'             # Single task")
            print("  python main.py --pipeline '...'         # Full pipeline mode")
            print("  python main.py --backend my-api          # Quick backend")
            print("  python main.py --check                  # Environment check")
            print()
            print("Pipeline Examples:")
            print('  python main.py --pipeline "Create an Express API with user authentication,')
            print('    start it locally, test the endpoints, create a GitHub repo called my-api,')
            print('    push all the code, and deploy to Vercel"')
            print()
            print("Environment Variables:")
            print("  OMNI_PROVIDER     - LLM provider (openai, anthropic, groq, ollama)")
            print("  OMNI_MODEL        - Model name override")
            print("  OMNI_API_KEY      - API key override")
            print("  OMNI_AUTO_APPROVE - Set to 'true' to skip approvals")
            print()
            return

    if args.backend:
        asyncio.run(create_and_run_backend(args.backend, args.framework, args.port))
    elif args.pipeline:
        asyncio.run(run_pipeline(args.pipeline, args.provider, args.model))
    elif args.task:
        asyncio.run(execute_single_task(args.task, args.provider, args.model))
    elif args.cli:
        from ui.cli import main as cli_main
        asyncio.run(cli_main())
    elif args.web:
        import subprocess
        subprocess.run(["streamlit", "run", "ui/web.py", "--server.port", "8501"])

if __name__ == "__main__":
    main()
