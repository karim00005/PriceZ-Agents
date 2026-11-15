from typing import Optional, List, Dict, Any
from core.agent import Agent

class Task:
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        agent: Agent,
        expected_output: str,
        context: Optional[List["Task"]] = None
    ):
        self.id = id
        self.name = name
        self.description = description
        self.agent = agent
        self.expected_output = expected_output
        self.context = context or []
        self.output: Optional[str] = None
        self.status = "pending"  # pending, in_progress, completed, failed

    def build_prompt(self, user_request: str) -> str:
        prompt_parts = [
            f"=== ORIGINAL USER REQUEST ===\n{user_request}\n",
            f"=== CURRENT TASK: {self.name} ===\n{self.description}\n",
            f"=== EXPECTED OUTPUT ===\n{self.expected_output}\n"
        ]

        if self.context:
            prompt_parts.append("=== PREVIOUS DELIVERABLES / CONTEXT ===")
            for prev_task in self.context:
                if prev_task.output:
                    prompt_parts.append(f"\n--- Output from [{prev_task.name} ({prev_task.agent.name})] ---:\n{prev_task.output}\n")

        return "\n".join(prompt_parts)

    async def run(self, user_request: str) -> str:
        self.status = "in_progress"
        await self.agent.notify_step("working", f"Starting execution of: {self.name}")
        prompt = self.build_prompt(user_request)
        self.output = await self.agent.execute(prompt)
        self.status = "completed"
        return self.output
