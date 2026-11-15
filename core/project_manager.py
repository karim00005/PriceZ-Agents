import os
import zipfile
import io
import json
import shutil
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from core.tools import AgentWorkspaceTools
from core.sync_engine import ProjectSyncEngine
from core.revisions import RevisionManager

class ProjectManager:
    def __init__(self, base_workspaces_dir: Optional[Path] = None, data_dir: Optional[Path] = None):
        self.base_dir = base_workspaces_dir or (Path(__file__).parent.parent / "workspaces")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir = data_dir or (Path(__file__).parent.parent / "data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.meta_file = self.data_dir / "projects_meta.json"
        
        self.sync_engine = ProjectSyncEngine(self.base_dir)
        self.revisions = RevisionManager(self.data_dir)
        self.running_processes: Dict[str, asyncio.subprocess.Process] = {}
        self.projects_meta = self._load_meta()

    def _load_meta(self) -> Dict[str, Dict[str, Any]]:
        if self.meta_file.exists():
            try:
                with open(self.meta_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_meta(self):
        try:
            with open(self.meta_file, "w", encoding="utf-8") as f:
                json.dump(self.projects_meta, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[ProjectManager] Error saving metadata: {e}")

    def get_workspace_dir(self, project_id: str = "default_project") -> Path:
        safe_id = "".join(c for c in project_id if c.isalnum() or c in ("-", "_")) or "default_project"
        target = self.base_dir / safe_id
        target.mkdir(parents=True, exist_ok=True)
        return target

    def get_tools(self, project_id: str = "default_project") -> AgentWorkspaceTools:
        return AgentWorkspaceTools(self.get_workspace_dir(project_id))

    def list_all_projects(self) -> List[Dict[str, Any]]:
        projects_list = []
        self.get_workspace_dir("default_project")

        for entry in os.scandir(self.base_dir):
            if entry.is_dir():
                pid = entry.name
                meta = self.projects_meta.get(pid, {})
                files = self.list_project_files(pid)
                
                last_mtime = max([f.get("mtime", 0) for f in files], default=entry.stat().st_mtime)
                last_mod_str = datetime.fromtimestamp(last_mtime).strftime("%Y-%m-%d %H:%M")

                project_info = {
                    "id": pid,
                    "name": meta.get("name", pid.replace("-", " ").title()),
                    "description": meta.get("description", "مشروع مُدار بواسطة وكلاء PriceZ الذكية."),
                    "created_at": meta.get("created_at", datetime.fromtimestamp(entry.stat().st_ctime).isoformat()),
                    "last_modified": last_mod_str,
                    "file_count": len(files),
                    "sync_status": meta.get("sync_status", "synced"),
                    "remote_url": meta.get("remote_url", "")
                }
                projects_list.append(project_info)

        projects_list.sort(key=lambda x: x["last_modified"], reverse=True)
        return projects_list

    def create_project(self, project_id: str, name: str, description: str = "") -> Dict[str, Any]:
        safe_id = "".join(c for c in project_id.lower() if c.isalnum() or c in ("-", "_")).strip("-")
        if not safe_id:
            safe_id = f"project_{int(datetime.now().timestamp())}"

        ws_dir = self.get_workspace_dir(safe_id)

        readme_file = ws_dir / "README.md"
        if not readme_file.exists():
            readme_file.write_text(f"""# {name}

{description or 'مشروع ذكي جديد تم إنشاؤه عبر منصة PriceZ Autonomous Agents.'}

## البدء السريع
- تم إنشاء المشروع في: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- طاقم العمل جاهز لتنفيذ الأوامر.
""", encoding="utf-8")

        self.projects_meta[safe_id] = {
            "name": name,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "sync_status": "local",
            "remote_url": ""
        }
        self._save_meta()

        # Initial revision
        self.revisions.create_snapshot(safe_id, ws_dir, "المشروع الأولي (Initial Commit)", "Boss")

        return {
            "success": True,
            "id": safe_id,
            "name": name,
            "workspace_path": str(ws_dir),
            "message": f"تم إنشاء المشروع '{name}' بنجاح."
        }

    def delete_project(self, project_id: str) -> Dict[str, Any]:
        if project_id == "default_project":
            return {"success": False, "error": "لا يمكن حذف المشروع الافتراضي."}

        safe_id = "".join(c for c in project_id if c.isalnum() or c in ("-", "_"))
        ws_dir = self.base_dir / safe_id
        if ws_dir.exists():
            try:
                shutil.rmtree(ws_dir)
            except Exception as e:
                return {"success": False, "error": str(e)}

        if safe_id in self.projects_meta:
            del self.projects_meta[safe_id]
            self._save_meta()

        return {"success": True, "message": f"تم حذف المشروع {safe_id} بنجاح."}

    def list_project_files(self, project_id: str = "default_project") -> List[Dict[str, Any]]:
        ws = self.get_workspace_dir(project_id)
        files_data = []
        for root, _, files in os.walk(ws):
            for f in files:
                full_path = Path(root) / f
                rel = full_path.relative_to(ws).as_posix()
                if "__pycache__" in rel or ".git" in rel:
                    continue

                try:
                    content = full_path.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    content = "[Binary or unreadable file]"
                
                stat = full_path.stat()
                files_data.append({
                    "path": rel,
                    "name": f,
                    "size": stat.st_size,
                    "mtime": stat.st_mtime,
                    "extension": full_path.suffix,
                    "content": content
                })
        files_data.sort(key=lambda x: x["path"])
        return files_data

    async def save_file_content(self, project_id: str, rel_path: str, content: str) -> Dict[str, Any]:
        """Saves edited file content directly to disk."""
        tools = self.get_tools(project_id)
        res = await tools.write_file(rel_path, content)
        return res

    def batch_write_files(self, project_id: str, files_list: List[Dict[str, Any]]) -> int:
        ws = self.get_workspace_dir(project_id)
        written = 0
        for item in files_list:
            rel_path = item.get("path", "").lstrip("/\\")
            content = item.get("content", "")
            if rel_path:
                target = ws / rel_path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
                written += 1
        return written

    def generate_zip_bytes(self, project_id: str = "default_project") -> bytes:
        ws = self.get_workspace_dir(project_id)
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for root, _, files in os.walk(ws):
                for file in files:
                    full_path = Path(root) / file
                    rel_path = full_path.relative_to(ws)
                    if "__pycache__" in str(rel_path):
                        continue
                    zip_file.write(full_path, arcname=str(rel_path))
        zip_buffer.seek(0)
        return zip_buffer.getvalue()

    def open_in_file_explorer(self, project_id: str = "default_project") -> bool:
        ws = self.get_workspace_dir(project_id)
        try:
            if os.name == 'nt':
                os.startfile(str(ws))
                return True
            else:
                import subprocess
                subprocess.Popen(["xdg-open", str(ws)])
                return True
        except Exception as e:
            print(f"[ProjectManager] Failed to open explorer: {e}")
            return False

    async def run_server_process(self, project_id: str = "default_project", command: str = "python main.py") -> Dict[str, Any]:
        ws = self.get_workspace_dir(project_id)
        if project_id in self.running_processes:
            p = self.running_processes[project_id]
            if p.returncode is None:
                p.terminate()

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                cwd=str(ws),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            self.running_processes[project_id] = process
            await asyncio.sleep(1.0)
            is_active = process.returncode is None
            return {
                "success": True,
                "pid": process.pid,
                "is_active": is_active,
                "message": f"تم تشغيل السيرفر بنجاح (PID: {process.pid})"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def stop_server_process(self, project_id: str = "default_project") -> Dict[str, Any]:
        if project_id in self.running_processes:
            p = self.running_processes[project_id]
            if p.returncode is None:
                p.terminate()
                return {"success": True, "message": f"تم إيقاف المعالجة {p.pid}."}
        return {"success": False, "message": "لا يوجد خادم قيد التشغيل لهذا المشروع."}

    async def execute_terminal_command(self, project_id: str, command: str, timeout: float = 30.0) -> Dict[str, Any]:
        """Runs an arbitrary terminal command inside workspace and returns output."""
        tools = self.get_tools(project_id)
        res = await tools.run_command(command, timeout=timeout)
        return res
