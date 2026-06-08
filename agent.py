import os
import json
import asyncio
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import traceback

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
            return {"error": str(e), "traceback": traceback.format_exc()}

class OmniAgent:
    def __init__(self, llm_client, config: Dict = None):
        self.llm = llm_client
        self.config = config or {}
        self.tools: Dict[str, Tool] = {}
        self.tasks: Dict[str, Task] = {}
        self.memory: List[Dict] = []
        self.max_iterations = self.config.get("max_iterations", 50)
        self.auto_approve = self.config.get("auto_approve", False)
        self.approval_callbacks: List[Callable] = []

    def register_tool(self, tool: Tool):
        self.tools[tool.name] = tool
        print(f"Registered tool: {tool.name}")

    def register_approval_callback(self, callback: Callable):
        self.approval_callbacks.append(callback)

    async def request_approval(self, action: str, details: Dict) -> bool:
        if self.auto_approve:
            return True
        for callback in self.approval_callbacks:
            if asyncio.iscoroutinefunction(callback):
                result = await callback(action, details)
            else:
                result = callback(action, details)
            if not result:
                return False
        return True

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
                    self.memory.append({"task": description, "result": task.result})
                    return task

                for tool_call in tool_calls:
                    tool_name = tool_call["function"]["name"]
                    tool_args = json.loads(tool_call["function"]["arguments"])

                    if tool_name in ["file_write", "file_delete", "github_push", "deploy", "shell_execute"]:
                        approved = await self.request_approval(tool_name, tool_args)
                        if not approved:
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call["id"],
                                "content": "Operation denied by user approval system."
                            })
                            continue

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
        return """You are OmniAgent, a powerful autonomous AI agent capable of:
- File operations (read, write, list, search)
- Code generation and execution
- Web search and research
- GitHub operations (repos, commits, PRs, issues)
- Deployment to various platforms
- Shell command execution
- Task planning and multi-step execution

When given a task:
1. Analyze what needs to be done
2. Break it into steps if needed
3. Use the appropriate tools
4. Verify results
5. Report completion with details

Be thorough but efficient. If a task requires multiple steps, plan them out first.
Always verify file operations succeeded before proceeding.
For code generation, write clean, documented code with error handling."""

    def get_task_status(self, task_id: str) -> Optional[Task]:
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> List[Task]:
        return list(self.tasks.values())
