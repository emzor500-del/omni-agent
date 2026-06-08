import os
import sys
import asyncio
import json
from datetime import datetime
from typing import Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agent import OmniAgent
from core.llm_client import LLMClient
from tools.tool_registry import get_all_tools
from tools.backend_tools import backend_create, backend_start, backend_stop, backend_status, backend_test

def print_banner():
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║   ██████╗ ███╗   ███╗███╗   ██╗██╗      █████╗  ██████╗ ███████╗███╗   ██╗████████╗║
    ║  ██╔═══██╗████╗ ████║████╗  ██║██║     ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝║
    ║  ██║   ██║██╔████╔██║██╔██╗ ██║██║     ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║   ║
    ║  ██║   ██║██║╚██╔╝██║██║╚██╗██║██║     ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║   ║
    ║  ╚██████╔╝██║ ╚═╝ ██║██║ ╚████║███████╗██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║   ║
    ║   ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝   ║
    ║                                                              ║
    ║         Autonomous AI Agent - Backend + Pipeline v1.1        ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

def print_help():
    print("""
Commands:
  /help              - Show this help
  /tools             - List available tools
  /tasks             - Show task history
  /task <id>         - Show task details
  /config            - Show current configuration
  /auto              - Toggle auto-approve mode
  /clear             - Clear screen
  /quit              - Exit

Backend Commands:
  /backend create <name> [framework] [port]  - Create new backend
  /backend start <path> [port]               - Start backend server
  /backend stop <name>                       - Stop backend server
  /backend status [name]                       - Check backend status
  /backend test <url>                          - Test endpoint
  /backend add-route <path> <route> [method]   - Add route to backend

Pipeline Mode:
  Just describe a full workflow and the agent will execute it:
  "Create an Express API, start it, test it, push to GitHub, deploy to Vercel"

Environment Variables:
  OPENAI_API_KEY      - OpenAI API key
  ANTHROPIC_API_KEY   - Anthropic/Claude API key
  GITHUB_TOKEN        - GitHub personal access token
  VERCEL_TOKEN        - Vercel deployment token
  NETLIFY_AUTH_TOKEN  - Netlify deployment token
  HEROKU_API_KEY      - Heroku API key
""")

def print_task(task):
    status_icon = {
        "pending": "⏳",
        "running": "🔄",
        "completed": "✅",
        "failed": "❌"
    }.get(task.status, "❓")

    print(f"\n{status_icon} Task: {task.id}")
    print(f"   Description: {task.description[:80]}...")
    print(f"   Status: {task.status}")
    print(f"   Created: {task.created_at}")
    if task.completed_at:
        print(f"   Completed: {task.completed_at}")
    if task.error:
        print(f"   Error: {task.error}")
    if task.tool_calls:
        print(f"   Tools used: {len(task.tool_calls)}")
        for tc in task.tool_calls:
            print(f"     - {tc['tool']}: {json.dumps(tc['args'])[:60]}")

def approval_callback(action: str, details: Dict) -> bool:
    print(f"\n🔒 Approval required for: {action}")
    print(f"   Details: {json.dumps(details, indent=2)[:200]}")
    response = input("   Approve? (y/n): ").strip().lower()
    return response in ['y', 'yes', '1', 'true']

async def handle_backend_command(parts, agent):
    """Handle backend-specific commands."""
    if len(parts) < 2:
        print("Usage: /backend <create|start|stop|status|test|add-route> ...")
        return

    subcmd = parts[1]

    if subcmd == "create" and len(parts) >= 3:
        name = parts[2]
        framework = parts[3] if len(parts) > 3 else "express"
        port = int(parts[4]) if len(parts) > 4 else 3000

        project_path = os.path.join(os.getcwd(), name)
        result = await backend_create(project_path, framework=framework, port=port)

        if result.get("success"):
            print(f"✅ Created {framework} backend at {project_path}")
            print(f"   Files: {', '.join(result['files_created'])}")
            print(f"   Start with: /backend start {project_path}")
        else:
            print(f"❌ Error: {result.get('error')}")

    elif subcmd == "start" and len(parts) >= 3:
        path = parts[2]
        port = int(parts[3]) if len(parts) > 3 else None

        result = await backend_start(path, port=port)
        if result.get("success"):
            print(f"✅ Server started!")
            print(f"   PID: {result['pid']}")
            print(f"   Port: {result['port']}")
        else:
            print(f"❌ Error: {result.get('error')}")

    elif subcmd == "stop" and len(parts) >= 3:
        name = parts[2]
        result = await backend_stop(project_name=name)
        if result.get("success"):
            print(f"✅ Stopped {name}")
        else:
            print(f"❌ Error: {result.get('error')}")

    elif subcmd == "status":
        name = parts[2] if len(parts) > 2 else None
        result = await backend_status(project_name=name)
        if "backends" in result:
            print(f"Running backends: {result['count']}")
            for b in result["backends"]:
                print(f"  {b['project']}: {b['status']} (PID: {b['pid']})")
        else:
            print(f"Status: {result}")

    elif subcmd == "test" and len(parts) >= 3:
        url = parts[2]
        result = await backend_test(url)
        print(f"Status: {result.get('status', 'N/A')}")
        print(f"Body: {result.get('body', 'N/A')[:500]}")

    elif subcmd == "add-route" and len(parts) >= 4:
        path = parts[2]
        route = parts[3]
        method = parts[4] if len(parts) > 4 else "GET"
        from tools.backend_tools import backend_add_route
        result = await backend_add_route(path, route, method)
        if result.get("success"):
            print(f"✅ Added route {method} {route}")
        else:
            print(f"❌ Error: {result.get('error')}")

    else:
        print("Unknown backend command. Type /help for usage.")

async def main():
    print_banner()

    # Configuration
    provider = os.getenv("OMNI_PROVIDER", "openai")
    model = os.getenv("OMNI_MODEL", None)
    api_key = os.getenv("OMNI_API_KEY", None)
    auto_approve = os.getenv("OMNI_AUTO_APPROVE", "false").lower() == "true"

    print(f"Provider: {provider}")
    print(f"Model: {model or 'default'}")
    print(f"Auto-approve: {auto_approve}")
    print("Type /help for commands\n")

    # Initialize
    llm = LLMClient(provider=provider, api_key=api_key, model=model)
    agent = OmniAgent(llm, config={"auto_approve": auto_approve, "max_iterations": 100})

    # Register tools
    for tool in get_all_tools():
        agent.register_tool(tool)

    # Register approval callback if not auto-approve
    if not auto_approve:
        agent.register_approval_callback(approval_callback)

    # Main loop
    while True:
        try:
            user_input = input("\n🤖 OmniAgent > ").strip()

            if not user_input:
                continue

            # Commands
            if user_input.startswith("/"):
                parts = user_input.split()
                cmd = parts[0]

                if cmd == "/help":
                    print_help()
                elif cmd == "/tools":
                    print("\nAvailable Tools:")
                    for tool in agent.tools.values():
                        print(f"  • {tool.name}: {tool.description[:60]}...")
                elif cmd == "/tasks":
                    tasks = agent.get_all_tasks()
                    if not tasks:
                        print("No tasks yet.")
                    else:
                        for task in tasks[-10:]:
                            print_task(task)
                elif cmd == "/task" and len(parts) > 1:
                    task_id = parts[1]
                    task = agent.get_task_status(task_id)
                    if task:
                        print_task(task)
                        if task.result:
                            print(f"\nResult:\n{task.result[:500]}")
                    else:
                        print(f"Task {task_id} not found.")
                elif cmd == "/config":
                    print(f"\nConfiguration:")
                    print(f"  Provider: {provider}")
                    print(f"  Model: {model or 'default'}")
                    print(f"  Auto-approve: {auto_approve}")
                    print(f"  Max iterations: {agent.max_iterations}")
                    print(f"  Tools registered: {len(agent.tools)}")
                elif cmd == "/auto":
                    auto_approve = not auto_approve
                    agent.auto_approve = auto_approve
                    print(f"Auto-approve: {'ON' if auto_approve else 'OFF'}")
                elif cmd == "/clear":
                    os.system('clear' if os.name != 'nt' else 'cls')
                    print_banner()
                elif cmd in ["/quit", "/exit", "/q"]:
                    print("Goodbye!")
                    break
                elif cmd == "/backend":
                    await handle_backend_command(parts, agent)
                else:
                    print("Unknown command. Type /help for available commands.")
                continue

            # Execute task (including pipeline tasks)
            task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            print(f"\n🚀 Executing task: {task_id}")
            print("   Working... (this may take a while for pipelines)")

            # Add pipeline context for complex tasks
            context = None
            if any(keyword in user_input.lower() for keyword in ["create", "build", "backend", "api", "server", "deploy", "push", "github"]):
                context = {
                    "mode": "pipeline_capable",
                    "hint": "You can create backends, start them, test endpoints, create GitHub repos, push code, and deploy. Use multiple tools in sequence."
                }

            task = await agent.execute_task(task_id, user_input, context=context)

            # Display result
            print(f"\n{'✅' if task.status == 'completed' else '❌'} Task {task.status.upper()}")

            if task.status == "completed":
                print(f"\n📋 Result:\n{task.result}")
            elif task.error:
                print(f"\n❌ Error: {task.error}")

            if task.tool_calls:
                print(f"\n🔧 Tools used ({len(task.tool_calls)}):")
                for i, tc in enumerate(task.tool_calls, 1):
                    status = "✅" if "error" not in str(tc.get("result", "")) else "❌"
                    print(f"   {i}. {status} {tc['tool']}")

        except KeyboardInterrupt:
            print("\nInterrupted.")
            continue
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
