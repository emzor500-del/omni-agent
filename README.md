# 🤖 OmniAgent

A powerful autonomous AI agent capable of executing complex multi-step tasks including file operations, code generation, web search, **backend development**, GitHub integration, and deployment to various platforms.

## What's New in v1.1

### 🖥️ Backend Development
- **Create backends** from scratch (Express.js or FastAPI)
- **Auto-generate** API routes, health checks, CORS, auth scaffolding
- **Start/stop** servers with process management
- **Test endpoints** automatically
- **Add routes** dynamically to existing backends

### 🔄 Pipeline Mode
Execute full workflows in one command:
```
Create backend → Start server → Test → Push to GitHub → Deploy
```

## Features

| Category | Tools | Capabilities |
|----------|-------|-------------|
| **File Operations** | 8 tools | Read, write, search, delete, move, copy files |
| **Backend Dev** | 6 tools | Create, start, stop, test, add routes, status |
| **GitHub** | 10 tools | Repos, files, branches, PRs, issues, push directories |
| **Web & Search** | 2 tools | DuckDuckGo search, URL fetching |
| **Shell & Code** | 3 tools | Shell execution, Python/JS code execution |
| **Deployment** | 5 tools | Vercel, Heroku, Netlify, GitHub Pages, Docker |

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set API Keys

```bash
export OPENAI_API_KEY="your-key"
# or
export ANTHROPIC_API_KEY="your-key"

# Optional - for GitHub and deployment
export GITHUB_TOKEN="your-github-token"
export VERCEL_TOKEN="your-vercel-token"
```

### 3. Run

```bash
# CLI mode
python main.py --cli

# Web UI
python main.py --web

# Single task
python main.py --task "Create a Python web scraper"

# Full pipeline
python main.py --pipeline "Create Express API, start it, push to GitHub, deploy to Vercel"

# Quick backend
python main.py --backend my-api --framework express --port 3000

# Check environment
python main.py --check
```

## Pipeline Examples

### 1. Backend → GitHub → Vercel
```bash
python main.py --pipeline "Create an Express.js API with user authentication, 
start it locally on port 3000, test the /health endpoint, 
create a GitHub repo called my-api, push all the code, 
and deploy to Vercel"
```

### 2. FastAPI → Heroku
```bash
python main.py --pipeline "Build a FastAPI backend with CRUD operations for a todo app,
start the server, test the endpoints, create a GitHub repo,
push the code, and deploy to Heroku"
```

### 3. Inside CLI
```
🤖 OmniAgent > Create an Express API, add a /products route with GET and POST,
start the server, test it, create a GitHub repo called store-api,
push all files, and deploy to Vercel
```

## Backend Commands (CLI)

```
/backend create my-api express 3000     # Create Express backend
/backend create my-api fastapi 8000      # Create FastAPI backend
/backend start ./my-api 3000             # Start server
/backend stop my-api                     # Stop server
/backend status                          # List all backends
/backend test http://localhost:3000/health # Test endpoint
/backend add-route ./my-api /api/items POST  # Add route
```

## Architecture

```
omni-agent/
├── core/
│   ├── agent.py         # Core agent with tool execution loop
│   └── llm_client.py    # Multi-provider LLM (OpenAI, Anthropic, Groq, Ollama)
├── tools/
│   ├── file_tools.py     # File operations
│   ├── backend_tools.py  # Backend development (NEW)
│   ├── github_tools.py   # GitHub API integration
│   ├── web_shell_tools.py # Web search, shell, code execution
│   ├── deploy_tools.py   # Deployment platforms
│   └── tool_registry.py  # All 34 tools registered
├── ui/
│   ├── cli.py           # Command-line interface
│   └── web.py           # Streamlit web interface
├── main.py              # Entry point with pipeline mode
└── requirements.txt
```

## Safety

- **Destructive operations** require approval by default
- **Set `OMNI_AUTO_APPROVE=true`** to skip approvals (use with caution)
- **Shell commands** have safety blocks for dangerous operations
- **Code execution** is sandboxed to temporary files
- **Backend servers** run in subprocesses with proper cleanup

## License

MIT
