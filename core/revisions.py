import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

class RevisionManager:
    def __init__(self, data_base_dir: Path):
        self.snapshots_dir = data_base_dir / "snapshots"
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

    def _get_project_snapshots_dir(self, project_id: str) -> Path:
        p_dir = self.snapshots_dir / project_id
        p_dir.mkdir(parents=True, exist_ok=True)
        return p_dir

    def create_snapshot(self, project_id: str, workspace_dir: Path, commit_msg: str, author: str = "Studio Team") -> Dict[str, Any]:
        """Creates an immutable snapshot of the project workspace."""
        rev_id = f"rev_{int(datetime.now().timestamp())}"
        target_dir = self._get_project_snapshots_dir(project_id) / rev_id
        target_dir.mkdir(parents=True, exist_ok=True)

        # Copy workspace files excluding pycache
        copied_files = 0
        for root, _, files in os.walk(workspace_dir):
            for file in files:
                if "__pycache__" in root or ".git" in root:
                    continue
                full_path = Path(root) / file
                rel_path = full_path.relative_to(workspace_dir)
                dest = target_dir / rel_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(full_path, dest)
                copied_files += 1

        meta = {
            "rev_id": rev_id,
            "project_id": project_id,
            "commit_msg": commit_msg,
            "author": author,
            "timestamp": datetime.now().isoformat(),
            "formatted_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "files_count": copied_files
        }

        with open(target_dir / "_meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        return meta

    def list_revisions(self, project_id: str) -> List[Dict[str, Any]]:
        """Lists all snapshots/revisions for a project."""
        p_dir = self._get_project_snapshots_dir(project_id)
        revisions = []
        for entry in os.scandir(p_dir):
            if entry.is_dir():
                meta_file = Path(entry.path) / "_meta.json"
                if meta_file.exists():
                    try:
                        with open(meta_file, "r", encoding="utf-8") as f:
                            revisions.append(json.load(f))
                    except Exception:
                        pass
        revisions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return revisions

    def rollback(self, project_id: str, rev_id: str, workspace_dir: Path) -> Dict[str, Any]:
        """Rolls back the workspace to a specific snapshot."""
        snap_dir = self._get_project_snapshots_dir(project_id) / rev_id
        if not snap_dir.exists():
            return {"success": False, "error": f"Snapshot '{rev_id}' does not exist."}

        # Clear existing workspace files
        for entry in os.scandir(workspace_dir):
            if entry.is_dir():
                shutil.rmtree(entry.path)
            else:
                os.remove(entry.path)

        # Restore from snapshot
        restored_count = 0
        for root, _, files in os.walk(snap_dir):
            for file in files:
                if file == "_meta.json":
                    continue
                full_path = Path(root) / file
                rel_path = full_path.relative_to(snap_dir)
                dest = workspace_dir / rel_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(full_path, dest)
                restored_count += 1

        return {
            "success": True,
            "message": f"تمت استعادة المشروع بنجاح إلى النسخة {rev_id} ({restored_count} ملفات)."
        }
