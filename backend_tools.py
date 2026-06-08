import os
import subprocess
import json
import time
import signal
from typing import Dict, List, Any, Optional

# Track running processes
running_processes: Dict[str, subprocess.Popen] = {}

async def backend_create(project_path: str, framework: str = "express", language: str = "javascript", 
                         port: int = 3000, features: List[str] = None) -> Dict:
    """Create a complete backend project from scratch."""
    try:
        features = features or ["api", "cors"]
        os.makedirs(project_path, exist_ok=True)

        if framework == "express" and language == "javascript":
            # Create Express.js backend
            package_json = {
                "name": os.path.basename(project_path),
                "version": "1.0.0",
                "description": "Auto-generated backend API",
                "main": "server.js",
                "scripts": {
                    "start": "node server.js",
                    "dev": "nodemon server.js"
                },
                "dependencies": {
                    "express": "^4.18.2",
                    "cors": "^2.8.5",
                    "dotenv": "^16.3.1"
                }
            }

            if "auth" in features:
                package_json["dependencies"]["jsonwebtoken"] = "^9.0.2"
                package_json["dependencies"]["bcryptjs"] = "^2.4.3"

            if "db" in features:
                package_json["dependencies"]["mongoose"] = "^8.0.0"

            server_code = """const express = require('express');
const cors = require('cors');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Health check
app.get('/health', (req, res) => {
    res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// API routes
app.get('/api', (req, res) => {
    res.json({ message: 'API is running', version: '1.0.0' });
});

app.get('/api/users', (req, res) => {
    res.json({ users: [] });
});

app.post('/api/users', (req, res) => {
    const { name, email } = req.body;
    res.status(201).json({ id: Date.now(), name, email });
});

// Error handling
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).json({ error: 'Something went wrong!' });
});

app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
    console.log(`Health check: http://localhost:${PORT}/health`);
});
"""

            with open(os.path.join(project_path, "package.json"), "w") as f:
                json.dump(package_json, f, indent=2)

            with open(os.path.join(project_path, "server.js"), "w") as f:
                f.write(server_code)

            with open(os.path.join(project_path, ".env"), "w") as f:
                f.write("PORT=3000\n")

            with open(os.path.join(project_path, ".gitignore"), "w") as f:
                f.write("node_modules/\n.env\n*.log\n")

            return {
                "framework": framework,
                "language": language,
                "port": port,
                "files_created": ["package.json", "server.js", ".env", ".gitignore"],
                "path": project_path,
                "start_command": "npm install && npm start",
                "success": True
            }

        elif framework == "fastapi" and language == "python":
            # Create FastAPI backend
            requirements = """fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
pydantic==2.5.0
"""

            if "db" in features:
                requirements += "sqlalchemy==2.0.23\nalembic==1.12.1\n"

            main_py = """from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from datetime import datetime

app = FastAPI(title="Auto-Generated API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class User(BaseModel):
    id: Optional[int] = None
    name: str
    email: str

users_db = []

@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/api")
async def api_root():
    return {"message": "API is running", "version": "1.0.0"}

@app.get("/api/users", response_model=List[User])
async def get_users():
    return users_db

@app.post("/api/users", response_model=User)
async def create_user(user: User):
    user.id = len(users_db) + 1
    users_db.append(user)
    return user

@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    for user in users_db:
        if user.id == user_id:
            return user
    raise HTTPException(status_code=404, detail="User not found")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""

            with open(os.path.join(project_path, "requirements.txt"), "w") as f:
                f.write(requirements)

            with open(os.path.join(project_path, "main.py"), "w") as f:
                f.write(main_py)

            with open(os.path.join(project_path, ".env"), "w") as f:
                f.write("PORT=8000\n")

            with open(os.path.join(project_path, ".gitignore"), "w") as f:
                f.write("__pycache__/\n.env\n*.pyc\nvenv/\n.venv/\n")

            return {
                "framework": framework,
                "language": language,
                "port": port,
                "files_created": ["requirements.txt", "main.py", ".env", ".gitignore"],
                "path": project_path,
                "start_command": "pip install -r requirements.txt && python main.py",
                "success": True
            }

        else:
            return {"error": f"Unsupported framework/language combo: {framework}/{language}"}

    except Exception as e:
        return {"error": str(e)}

async def backend_start(project_path: str, command: str = None, port: int = None, 
                        framework: str = None, env_vars: Dict = None) -> Dict:
    """Start a backend server process."""
    try:
        project_name = os.path.basename(project_path)

        # Auto-detect if not specified
        if not framework:
            if os.path.exists(os.path.join(project_path, "server.js")):
                framework = "express"
            elif os.path.exists(os.path.join(project_path, "main.py")):
                framework = "fastapi"
            elif os.path.exists(os.path.join(project_path, "package.json")):
                framework = "express"

        # Auto-detect command
        if not command:
            if framework == "express":
                command = "npm start"
            elif framework == "fastapi":
                command = "python main.py"
            else:
                return {"error": "Could not auto-detect start command. Please specify."}

        # Check if already running
        if project_name in running_processes:
            proc = running_processes[project_name]
            if proc.poll() is None:
                return {
                    "error": f"Server already running for {project_name}",
                    "pid": proc.pid,
                    "status": "running"
                }

        # Setup environment
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)
        if port:
            env["PORT"] = str(port)

        # Install dependencies first if needed
        if framework == "express" and os.path.exists(os.path.join(project_path, "package.json")):
            if not os.path.exists(os.path.join(project_path, "node_modules")):
                install_result = subprocess.run(
                    ["npm", "install"],
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                if install_result.returncode != 0:
                    return {"error": "npm install failed", "stderr": install_result.stderr[:1000]}

        elif framework == "fastapi":
            try:
                __import__("fastapi")
            except ImportError:
                install_result = subprocess.run(
                    ["pip", "install", "-r", "requirements.txt"],
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                if install_result.returncode != 0:
                    return {"error": "pip install failed", "stderr": install_result.stderr[:1000]}

        # Start the server
        proc = subprocess.Popen(
            command,
            cwd=project_path,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            preexec_fn=os.setsid if os.name != 'nt' else None
        )

        running_processes[project_name] = proc

        # Wait a moment to check if it started successfully
        time.sleep(2)

        if proc.poll() is not None:
            stdout, stderr = proc.communicate()
            return {
                "error": "Server failed to start",
                "stdout": stdout[:2000],
                "stderr": stderr[:2000],
                "returncode": proc.returncode
            }

        return {
            "project": project_name,
            "pid": proc.pid,
            "command": command,
            "port": port or "auto",
            "status": "running",
            "path": project_path,
            "success": True
        }

    except Exception as e:
        return {"error": str(e)}

async def backend_stop(project_name: str = None, pid: int = None) -> Dict:
    """Stop a running backend server."""
    try:
        if project_name and project_name in running_processes:
            proc = running_processes[project_name]
            if proc.poll() is None:
                if os.name != 'nt':
                    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                else:
                    proc.terminate()

                proc.wait(timeout=5)
                del running_processes[project_name]
                return {"project": project_name, "pid": proc.pid, "status": "stopped", "success": True}
            else:
                del running_processes[project_name]
                return {"project": project_name, "status": "already_stopped"}

        elif pid:
            if os.name != 'nt':
                os.kill(pid, signal.SIGTERM)
            else:
                import ctypes
                ctypes.windll.kernel32.TerminateProcess(ctypes.windll.kernel32.OpenProcess(1, False, pid), 0)
            return {"pid": pid, "status": "stopped", "success": True}

        else:
            return {"error": "Specify project_name or pid"}

    except Exception as e:
        return {"error": str(e)}

async def backend_status(project_name: str = None) -> Dict:
    """Check status of running backends."""
    try:
        if project_name:
            if project_name in running_processes:
                proc = running_processes[project_name]
                is_running = proc.poll() is None
                return {
                    "project": project_name,
                    "pid": proc.pid,
                    "status": "running" if is_running else "stopped",
                    "returncode": proc.returncode if not is_running else None
                }
            return {"project": project_name, "status": "not_found"}

        statuses = []
        for name, proc in list(running_processes.items()):
            is_running = proc.poll() is None
            statuses.append({
                "project": name,
                "pid": proc.pid,
                "status": "running" if is_running else "stopped"
            })
            if not is_running:
                del running_processes[name]

        return {"backends": statuses, "count": len(statuses)}

    except Exception as e:
        return {"error": str(e)}

async def backend_test(endpoint: str, method: str = "GET", data: Dict = None, 
                       headers: Dict = None, timeout: int = 10) -> Dict:
    """Test a backend endpoint."""
    try:
        import aiohttp

        async with aiohttp.ClientSession() as session:
            if method.upper() == "GET":
                async with session.get(endpoint, headers=headers, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                    return {
                        "endpoint": endpoint,
                        "method": method,
                        "status": resp.status,
                        "body": (await resp.text())[:5000],
                        "headers": dict(resp.headers)
                    }
            elif method.upper() == "POST":
                async with session.post(endpoint, json=data, headers=headers, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                    return {
                        "endpoint": endpoint,
                        "method": method,
                        "status": resp.status,
                        "body": (await resp.text())[:5000],
                        "headers": dict(resp.headers)
                    }
            else:
                return {"error": f"Unsupported method: {method}"}

    except Exception as e:
        return {"error": str(e), "endpoint": endpoint}

async def backend_add_route(project_path: str, route: str, method: str = "GET", 
                            handler_code: str = None, framework: str = "express") -> Dict:
    """Add a new route to an existing backend."""
    try:
        if framework == "express":
            server_file = os.path.join(project_path, "server.js")
            if not os.path.exists(server_file):
                return {"error": "server.js not found"}

            with open(server_file, "r") as f:
                content = f.read()

            # Add route before the error handler or listen
            route_code = f"""
// Added route: {route}
app.{method.lower()}('{route}', (req, res) => {{
    {handler_code or "res.json({ message: 'New route', route: '" + route + "' });"}
}});
"""

            # Insert before error handler
            if "// Error handling" in content:
                content = content.replace("// Error handling", route_code + "\n// Error handling")
            else:
                content = content.replace("app.listen", route_code + "\napp.listen")

            with open(server_file, "w") as f:
                f.write(content)

            return {"route": route, "method": method, "file": server_file, "success": True}

        elif framework == "fastapi":
            main_file = os.path.join(project_path, "main.py")
            if not os.path.exists(main_file):
                return {"error": "main.py not found"}

            with open(main_file, "r") as f:
                content = f.read()

            route_code = f"""
@app.{method.lower()}("{route}")
async def {route.replace('/', '_').strip('_')}_handler():
    {handler_code or 'return {"message": "New route", "route": "' + route + '"}'}
"""

            # Insert before if __name__
            if 'if __name__ == "__main__":' in content:
                content = content.replace('if __name__ == "__main__":', route_code + '\nif __name__ == "__main__":')
            else:
                content += "\n" + route_code

            with open(main_file, "w") as f:
                f.write(content)

            return {"route": route, "method": method, "file": main_file, "success": True}

        else:
            return {"error": f"Unsupported framework: {framework}"}

    except Exception as e:
        return {"error": str(e)}
