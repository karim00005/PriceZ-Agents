import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

class SessionMemory:
    def __init__(self, data_file: Optional[Path] = None):
        self.data_file = data_file or (Path(__file__).parent.parent / "data" / "sessions.json")
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.sessions: Dict[str, Dict[str, Any]] = self._load()

    def _load(self) -> Dict[str, Dict[str, Any]]:
        if self.data_file.exists():
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save(self):
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(self.sessions, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[SessionMemory] Failed to save session: {e}")

    def get_or_create_session(self, session_id: str = "default_session") -> Dict[str, Any]:
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "id": session_id,
                "created_at": datetime.now().isoformat(),
                "history": [],
                "context_summary": "",
                "last_deliverables": {}
            }
            self._save()
        return self.sessions[session_id]

    def add_user_message(self, session_id: str, message: str):
        session = self.get_or_create_session(session_id)
        session["history"].append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        self._save()

    def add_agent_response(self, session_id: str, agent_id: str, content: str):
        session = self.get_or_create_session(session_id)
        session["history"].append({
            "role": "agent",
            "agent_id": agent_id,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self._save()

    def update_deliverables(self, session_id: str, deliverables: Dict[str, Any]):
        session = self.get_or_create_session(session_id)
        session["last_deliverables"] = deliverables
        self._save()

    def get_context_prompt(self, session_id: str) -> str:
        session = self.get_or_create_session(session_id)
        history = session.get("history", [])
        if not history:
            return ""

        context_lines = ["=== RECENT CONVERSATION HISTORY & PROJECT CONTEXT ==="]
        # Include last 6 turns
        for turn in history[-6:]:
            role = turn.get("role", "unknown")
            agent = f"[{turn.get('agent_id')}]" if "agent_id" in turn else ""
            content = turn.get("content", "")[:350]
            context_lines.append(f"{role.upper()} {agent}: {content}")
        return "\n".join(context_lines)
