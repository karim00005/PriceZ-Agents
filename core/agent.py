from typing import Callable, Optional, Any, Dict
from core.llm_provider import LLMProvider

class Agent:
    def __init__(
        self,
        id: str,
        name: str,
        role: str,
        goal: str,
        backstory: str,
        avatar: str = "🤖",
        step_callback: Optional[Callable[[Dict[str, Any]], Any]] = None,
        llm: Optional[LLMProvider] = None
    ):
        self.id = id
        self.name = name
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.avatar = avatar
        self.step_callback = step_callback
        self.llm = llm or LLMProvider()
        self.status = "idle"  # idle, thinking, working, done, error

    @property
    def system_prompt(self) -> str:
        return f"""You are {self.name}.
Role: {self.role}
Goal: {self.goal}
Backstory: {self.backstory}

Strict Operating Rules:
1. Stay strictly within your role.
2. Maintain high technical precision and professional excellence.
3. Be structured, clean, and concise.
"""

    async def notify_step(self, status: str, step_details: str):
        self.status = status
        if self.step_callback:
            await self.step_callback({
                "agent_id": self.id,
                "agent_name": self.name,
                "status": status,
                "step_details": step_details,
                "avatar": self.avatar
            })

    async def execute(self, task_prompt: str) -> str:
        await self.notify_step("thinking", "Analyzing inputs and initiating cognitive process...")
        
        async def on_step(detail: str):
            await self.notify_step("working", detail)

        result = await self.llm.generate_response(
            system_instruction=self.system_prompt,
            prompt=task_prompt,
            step_callback=on_step,
            agent_name=self.name
        )

        await self.notify_step("done", "Task completed.")
        return result
