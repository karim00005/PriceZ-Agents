import os
import subprocess
import asyncio
from pathlib import Path
from typing import Dict, Any, List

class AgentWorkspaceTools:
    def __init__(self, workspace_dir: Path):
        self.workspace_dir = workspace_dir
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, rel_path: str) -> Path:
        safe_rel = rel_path.lstrip("/\\")
        full_path = (self.workspace_dir / safe_rel).resolve()
        # Security: Prevent path traversal outside workspace
        if not str(full_path).startswith(str(self.workspace_dir.resolve())):
            raise ValueError(f"Access denied: Path '{rel_path}' is outside workspace.")
        return full_path

    async def write_file(self, rel_path: str, content: str) -> Dict[str, Any]:
        """Creates or updates a file in the project workspace."""
        try:
            target = self._resolve_path(rel_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            return {
                "success": True,
                "message": f"Successfully created/updated file: {rel_path}",
                "path": rel_path,
                "size_bytes": len(content.encode("utf-8"))
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def read_file(self, rel_path: str) -> Dict[str, Any]:
        """Reads a file from the workspace."""
        try:
            target = self._resolve_path(rel_path)
            if not target.exists():
                return {"success": False, "error": f"File '{rel_path}' does not exist."}
            content = target.read_text(encoding="utf-8")
            return {"success": True, "path": rel_path, "content": content}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def list_files(self, sub_dir: str = "") -> List[Dict[str, Any]]:
        """Lists all files in the workspace with metadata."""
        items = []
        target_dir = self._resolve_path(sub_dir) if sub_dir else self.workspace_dir
        if not target_dir.exists():
            return items

        for root, _, files in os.walk(target_dir):
            for file in files:
                full_file = Path(root) / file
                rel_path = full_file.relative_to(self.workspace_dir).as_posix()
                items.append({
                    "path": rel_path,
                    "name": file,
                    "size": full_file.stat().st_size,
                    "extension": full_file.suffix
                })
        return items

    async def run_command(self, command: str, timeout: float = 20.0) -> Dict[str, Any]:
        """Executes a shell command inside the project workspace safely across all OS event loops."""
        def _exec():
            try:
                proc = subprocess.run(
                    command,
                    shell=True,
                    cwd=str(self.workspace_dir),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=timeout
                )
                return {
                    "success": proc.returncode == 0,
                    "returncode": proc.returncode,
                    "stdout": proc.stdout,
                    "stderr": proc.stderr
                }
            except subprocess.TimeoutExpired:
                return {"success": False, "error": f"Command timed out after {timeout} seconds."}
            except Exception as e:
                return {"success": False, "error": str(e)}

        return await asyncio.to_thread(_exec)
