import os
import aiohttp
import json
from typing import Dict, List, Any, Optional

class LLMClient:
    def __init__(self, provider: str = "openai", api_key: str = None, model: str = None, base_url: str = None):
        self.provider = provider.lower()
        self.api_key = api_key or self._get_api_key()
        self.model = model or self._get_default_model()
        self.base_url = base_url or self._get_base_url()

    def _get_api_key(self) -> str:
        env_vars = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "claude": "ANTHROPIC_API_KEY",
            "groq": "GROQ_API_KEY",
            "ollama": "",
            "local": ""
        }
        return os.getenv(env_vars.get(self.provider, "OPENAI_API_KEY"), "")

    def _get_default_model(self) -> str:
        models = {
            "openai": "gpt-4o",
            "anthropic": "claude-3-5-sonnet-20241022",
            "claude": "claude-3-5-sonnet-20241022",
            "groq": "llama-3.3-70b-versatile",
            "ollama": "llama3.2",
            "local": "llama3.2"
        }
        return models.get(self.provider, "gpt-4o")

    def _get_base_url(self) -> str:
        urls = {
            "openai": "https://api.openai.com/v1",
            "anthropic": "https://api.anthropic.com/v1",
            "claude": "https://api.anthropic.com/v1",
            "groq": "https://api.groq.com/openai/v1",
            "ollama": "http://localhost:11434/v1",
            "local": "http://localhost:11434/v1"
        }
        return urls.get(self.provider, "https://api.openai.com/v1")

    async def chat_completion(self, messages: List[Dict], tools: List[Dict] = None, tool_choice: str = "auto") -> Dict:
        if self.provider in ["anthropic", "claude"]:
            return await self._anthropic_completion(messages, tools, tool_choice)
        else:
            return await self._openai_completion(messages, tools, tool_choice)

    async def _openai_completion(self, messages: List[Dict], tools: List[Dict], tool_choice: str) -> Dict:
        payload = {
            "model": self.model,
            "messages": messages,
            "tool_choice": tool_choice if tools else None
        }
        if tools:
            payload["tools"] = tools

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API Error {response.status}: {error_text}")
                return await response.json()

    async def _anthropic_completion(self, messages: List[Dict], tools: List[Dict], tool_choice: str) -> Dict:
        # Convert OpenAI format to Anthropic format
        system_msg = ""
        anthropic_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_msg += msg["content"] + "\n"
            else:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": [{"type": "text", "text": msg["content"]}]
                })

        # Convert tools to Anthropic format
        anthropic_tools = []
        if tools:
            for tool in tools:
                anthropic_tools.append({
                    "name": tool["function"]["name"],
                    "description": tool["function"]["description"],
                    "input_schema": tool["function"]["parameters"]
                })

        payload = {
            "model": self.model,
            "max_tokens": 4096,
            "system": system_msg,
            "messages": anthropic_messages,
            "tools": anthropic_tools if anthropic_tools else None
        }

        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/messages",
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API Error {response.status}: {error_text}")

                result = await response.json()
                # Convert back to OpenAI format
                return self._anthropic_to_openai(result)

    def _anthropic_to_openai(self, anthropic_response: Dict) -> Dict:
        content = anthropic_response.get("content", [])
        text_content = ""
        tool_calls = []

        for item in content:
            if item["type"] == "text":
                text_content += item["text"]
            elif item["type"] == "tool_use":
                tool_calls.append({
                    "id": item["id"],
                    "type": "function",
                    "function": {
                        "name": item["name"],
                        "arguments": json.dumps(item["input"])
                    }
                })

        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": text_content,
                    "tool_calls": tool_calls
                }
            }]
        }
