import os
import hashlib
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
import httpx

class ProjectSyncEngine:
    """
    Bidirectional synchronization engine connecting Local Desktop workspace
    with Remote Cloud server instances in real-time.
    """
    def __init__(self, workspace_base_dir: Path):
        self.workspace_base_dir = workspace_base_dir

    def _get_project_dir(self, project_id: str) -> Path:
        p_dir = self.workspace_base_dir / project_id
        p_dir.mkdir(parents=True, exist_ok=True)
        return p_dir

    def calculate_file_hash(self, file_path: Path) -> str:
        try:
            hasher = hashlib.sha256()
            with open(file_path, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return ""

    def get_manifest(self, project_id: str) -> Dict[str, Any]:
        """
        Builds a manifest containing SHA256 hashes and modification timestamps
        for all files in the project workspace.
        """
        p_dir = self._get_project_dir(project_id)
        files_manifest = {}

        for root, _, files in os.walk(p_dir):
            for f in files:
                full_path = Path(root) / f
                rel_path = full_path.relative_to(p_dir).as_posix()
                # Skip cache and git files
                if "__pycache__" in rel_path or ".git" in rel_path:
                    continue

                try:
                    stat = full_path.stat()
                    files_manifest[rel_path] = {
                        "hash": self.calculate_file_hash(full_path),
                        "mtime": stat.st_mtime,
                        "size": stat.st_size
                    }
                except Exception:
                    pass

        return {
            "project_id": project_id,
            "file_count": len(files_manifest),
            "files": files_manifest
        }

    async def push_to_remote(self, remote_url: str, project_id: str, auth_token: str = "") -> Dict[str, Any]:
        """
        Pushes modified local files up to the remote online server.
        """
        clean_url = remote_url.rstrip("/")
        p_dir = self._get_project_dir(project_id)
        local_manifest = self.get_manifest(project_id)

        # 1. Fetch remote manifest
        headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else {}
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.get(f"{clean_url}/api/projects/{project_id}/manifest", headers=headers)
                if resp.status_code == 200:
                    remote_manifest = resp.json().get("files", {})
                else:
                    remote_manifest = {}
            except Exception as e:
                return {"success": False, "error": f"تعذر الاتصال بالسيرفر السحابي ({clean_url}): {str(e)}"}

            # 2. Determine which files are new or modified
            files_to_upload = []
            for rel_path, local_info in local_manifest["files"].items():
                remote_info = remote_manifest.get(rel_path)
                if not remote_info or local_info["hash"] != remote_info["hash"]:
                    full_file = p_dir / rel_path
                    try:
                        content = full_file.read_text(encoding="utf-8", errors="replace")
                        files_to_upload.append({
                            "path": rel_path,
                            "content": content,
                            "mtime": local_info["mtime"]
                        })
                    except Exception:
                        pass

            if not files_to_upload:
                return {"success": True, "uploaded_count": 0, "message": "جميع الملفات متزامنة بالفعل مع السيرفر السحابي."}

            # 3. Send batch upload to remote
            push_resp = await client.post(
                f"{clean_url}/api/projects/{project_id}/sync/batch-upload",
                headers=headers,
                json={"files": files_to_upload}
            )

            if push_resp.status_code == 200:
                return {
                    "success": True,
                    "uploaded_count": len(files_to_upload),
                    "files": [f["path"] for f in files_to_upload],
                    "message": f"تم رفع {len(files_to_upload)} ملف بنجاح إلى النسخة السحابية."
                }
            else:
                return {"success": False, "error": f"فشل الرفع السحابي: {push_resp.text}"}

    async def pull_from_remote(self, remote_url: str, project_id: str, auth_token: str = "") -> Dict[str, Any]:
        """
        Pulls newer files down from the remote online server to local workspace.
        """
        clean_url = remote_url.rstrip("/")
        p_dir = self._get_project_dir(project_id)
        local_manifest = self.get_manifest(project_id)
        headers = {"Authorization": f"Bearer {auth_token}"} if auth_token else {}

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.get(f"{clean_url}/api/projects/{project_id}/files", headers=headers)
                if resp.status_code != 200:
                    return {"success": False, "error": f"فشل سحب الملفات من السيرفر: {resp.text}"}
                remote_data = resp.json()
                remote_files = remote_data.get("files", [])
            except Exception as e:
                return {"success": False, "error": f"تعذر الاتصال بالسيرفر السحابي ({clean_url}): {str(e)}"}

            updated_count = 0
            for r_file in remote_files:
                rel_path = r_file["path"]
                content = r_file.get("content", "")
                target_file = p_dir / rel_path
                target_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Check if hash differs
                current_hash = self.calculate_file_hash(target_file) if target_file.exists() else ""
                content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

                if current_hash != content_hash:
                    target_file.write_text(content, encoding="utf-8")
                    updated_count += 1

            return {
                "success": True,
                "updated_count": updated_count,
                "message": f"تم تحديث وسحب {updated_count} ملف من السيرفر السحابي بنجاح."
            }

    async def sync_bidirectional(self, remote_url: str, project_id: str, auth_token: str = "") -> Dict[str, Any]:
        """
        Two-way intelligent synchronization:
        1. Pushes local changes to remote.
        2. Pulls remote updates down to local.
        """
        push_res = await self.push_to_remote(remote_url, project_id, auth_token)
        pull_res = await self.pull_from_remote(remote_url, project_id, auth_token)
        
        return {
            "success": push_res.get("success", False) and pull_res.get("success", False),
            "pushed": push_res.get("uploaded_count", 0),
            "pulled": pull_res.get("updated_count", 0),
            "message": f"المزامنة الثنائية اكتملت (تم رفع {push_res.get('uploaded_count', 0)} وسحب {pull_res.get('updated_count', 0)} ملف)."
        }
