import asyncio
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

import config
from api.websocket_manager import ConnectionManager
from core.crew import OrchestratorCrew
from core.file_watcher import WorkspaceWatcher
from core.auth import AuthManager

app = FastAPI(
    title="PriceZ Autonomous AI Software Studio",
    description="Multi-Agent Studio with Autonomous Loops, Virtual Anime Office, Live IDE Editor, Integrated Terminal & Time Travel Snapshots",
    version="3.0.0"
)

auth_manager = AuthManager()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ws_manager = ConnectionManager()
crew = OrchestratorCrew(
    event_broadcaster=ws_manager.broadcast,
    provider=config.DEFAULT_PROVIDER,
    api_key=config.API_KEY,
    model=config.DEFAULT_MODEL,
    base_url=config.BASE_URL
)

# Start real-time file watcher on default workspace
file_watcher = WorkspaceWatcher(ws_manager.broadcast)
try:
    file_watcher.watch_directory(crew.project_manager.get_workspace_dir("default_project"))
except Exception as e:
    print(f"[FileWatcher Warning] {e}")

static_dir = Path(__file__).parent.parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# Pydantic Schemas
class RunRequest(BaseModel):
    prompt: str
    session_id: Optional[str] = "default_session"
    project_id: Optional[str] = "default_project"
    target_agent: Optional[str] = "all"
    provider: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None


class ConfigRequest(BaseModel):
    provider: Optional[str] = "gemini"
    api_key: Optional[str] = ""
    model: Optional[str] = "gemini-2.5-flash"
    base_url: Optional[str] = ""


class TestConnectionRequest(BaseModel):
    provider: Optional[str] = "gemini"
    api_key: Optional[str] = ""
    model: Optional[str] = "gemini-2.5-flash"
    base_url: Optional[str] = ""


class RunServerRequest(BaseModel):
    command: Optional[str] = "python main.py"


class SaveFileRequest(BaseModel):
    path: str
    content: str


class TerminalRunRequest(BaseModel):
    command: str
    timeout: Optional[float] = 30.0


class CreateProjectRequest(BaseModel):
    id: str
    name: str
    description: Optional[str] = ""


class SyncRequest(BaseModel):
    remote_url: str
    auth_token: Optional[str] = ""


class BatchUploadRequest(BaseModel):
    files: List[Dict[str, Any]]


class RenameAgentRequest(BaseModel):
    name: str
    title: Optional[str] = None
    role: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    name: Optional[str] = None
    role: Optional[str] = "مطور ومستخدم"


class CreateUserRequest(BaseModel):
    username: str
    password: str
    name: str
    role: Optional[str] = "مطور ومستخدم"
    is_admin: Optional[bool] = False


class UpdateUserRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    password: Optional[str] = None
    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None


class UserLLMConfigRequest(BaseModel):
    provider: Optional[str] = "gemini"
    api_key: Optional[str] = ""
    model: Optional[str] = "gemini-2.5-flash"
    base_url: Optional[str] = ""


def get_current_user_from_req(request: Request) -> Optional[Dict[str, Any]]:
    auth_header = request.headers.get("Authorization", "")
    token = None
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
    if not token:
        token = request.headers.get("X-Auth-Token", "")
    if not token:
        token = request.cookies.get("pricez_auth_token", "")
    if token:
        return auth_manager.get_user_by_token(token)
    return None


# ============================================================
# Core API Routes
# ============================================================

@app.get("/")
async def serve_dashboard():
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse({"status": "running", "message": "PriceZ Studio UI file not found."})


@app.get("/api/status")
async def get_status(request: Request):
    stats = crew.get_real_stats("default_project")
    user = get_current_user_from_req(request)
    return {
        "is_running": crew.is_running,
        "provider": crew.llm.provider,
        "model": crew.llm.model,
        "has_api_key": bool(crew.llm.api_key),
        "base_url": crew.llm.base_url,
        "agents": list(crew.agents_state.values()),
        "stats": stats,
        "user": user
    }


# ============================================================
# User Authentication & Per-User API Key Routes
# ============================================================

@app.post("/api/auth/login")
async def login_endpoint(req: LoginRequest):
    res = auth_manager.login(req.username, req.password)
    if not res.get("success"):
        raise HTTPException(status_code=401, detail=res.get("error", "بيانات الدخول غير صحيحة"))
    return res


@app.post("/api/auth/register")
async def register_endpoint(req: RegisterRequest):
    res = auth_manager.register(req.username, req.password, req.name, req.role)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "فشل إنشاء الحساب"))
    return res


@app.get("/api/auth/me")
async def get_current_user_endpoint(request: Request):
    user = get_current_user_from_req(request)
    if not user:
        raise HTTPException(status_code=401, detail="غير مسجل الدخول")
    return {"authenticated": True, "user": user}


@app.post("/api/auth/logout")
async def logout_endpoint(request: Request):
    auth_header = request.headers.get("Authorization", "")
    token = None
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
    if not token:
        token = request.headers.get("X-Auth-Token", "")
    if token and token in auth_manager.sessions:
        del auth_manager.sessions[token]
        auth_manager._save_sessions()
    return {"success": True, "message": "تم تسجيل الخروج بنجاح."}


# ============================================================
# User Management Endpoints (إدارة المستخدمين وصلاحيات الفريق)
# ============================================================

@app.get("/api/users")
async def list_users_endpoint(request: Request):
    users = auth_manager.list_users()
    return {"success": True, "users": users}


@app.post("/api/users")
async def create_user_endpoint(req: CreateUserRequest, request: Request):
    current_user = get_current_user_from_req(request)
    creator = current_user["username"] if current_user else "admin"
    res = auth_manager.create_user(
        creator_username=creator,
        username=req.username,
        password=req.password,
        name=req.name,
        role=req.role or "مطور ومستخدم",
        is_admin=bool(req.is_admin)
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res


@app.put("/api/users/{username}")
async def update_user_endpoint(username: str, req: UpdateUserRequest, request: Request):
    current_user = get_current_user_from_req(request)
    creator = current_user["username"] if current_user else "admin"
    res = auth_manager.update_user(
        creator_username=creator,
        target_username=username,
        name=req.name,
        role=req.role,
        password=req.password,
        is_admin=req.is_admin,
        is_active=req.is_active
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res


@app.delete("/api/users/{username}")
async def delete_user_endpoint(username: str, request: Request):
    current_user = get_current_user_from_req(request)
    creator = current_user["username"] if current_user else "admin"
    res = auth_manager.delete_user(creator_username=creator, target_username=username)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res


@app.get("/api/user/llm-config")
async def get_user_llm_config_endpoint(request: Request):
    user = get_current_user_from_req(request)
    if not user:
        return {
            "provider": crew.llm.provider,
            "has_api_key": bool(crew.llm.api_key),
            "model": crew.llm.model,
            "base_url": crew.llm.base_url,
            "is_personal": False
        }
    cfg = auth_manager.get_user_llm_config(user["username"])
    return {
        "provider": cfg.get("provider", crew.llm.provider),
        "has_api_key": bool(cfg.get("api_key")),
        "model": cfg.get("model", crew.llm.model),
        "base_url": cfg.get("base_url", ""),
        "is_personal": True,
        "username": user["username"]
    }


@app.post("/api/user/llm-config")
async def update_user_llm_config_endpoint(req: UserLLMConfigRequest, request: Request):
    user = get_current_user_from_req(request)
    username = user["username"] if user else "admin"
    res = auth_manager.update_user_llm_config(
        username=username,
        provider=req.provider,
        api_key=req.api_key,
        model=req.model,
        base_url=req.base_url
    )
    if req.api_key:
        crew.update_config(provider=req.provider, api_key=req.api_key, model=req.model, base_url=req.base_url)
    return res


@app.post("/api/agents/{agent_id}/rename")
async def rename_agent_endpoint(agent_id: str, req: RenameAgentRequest):
    res = crew.rename_agent(agent_id, req.name, req.title, req.role)
    if res.get("success"):
        await ws_manager.broadcast({
            "event": "agent_renamed",
            "agent_id": agent_id,
            "name": req.name,
            "title": req.title or req.name,
            "role": req.role
        })
    return res


@app.post("/api/config")
async def update_config(req: ConfigRequest):
    crew.update_config(
        provider=req.provider,
        api_key=req.api_key,
        model=req.model,
        base_url=req.base_url
    )
    return {
        "success": True,
        "provider": crew.llm.provider,
        "model": crew.llm.model,
        "has_api_key": bool(crew.llm.api_key)
    }


@app.get("/api/models")
async def get_available_models():
    from core.llm_provider import OPENROUTER_FREE_MODELS
    return {
        "success": True,
        "openrouter_free": OPENROUTER_FREE_MODELS,
        "default_models": {
            "gemini": "gemini-2.5-flash",
            "openrouter": "nvidia/nemotron-3-ultra-550b-a55b:free",
            "deepseek": "deepseek-chat",
            "anthropic": "claude-3-5-sonnet-20241022",
            "openai": "llama-3.3-70b-versatile"
        }
    }


@app.post("/api/test-connection")
async def test_connection(req: TestConnectionRequest):
    from core.llm_provider import LLMProvider
    test_provider = LLMProvider(
        provider=req.provider or crew.llm.provider,
        api_key=req.api_key or crew.llm.api_key,
        model=req.model or crew.llm.model,
        base_url=req.base_url or crew.llm.base_url
    )
    return await test_provider.test_connection()


@app.post("/api/stop")
async def stop_workflow():
    stopped = crew.stop()
    await ws_manager.broadcast({
        "event": "workflow_error",
        "error": "تم إيقاف المهمة بواسطة المدير."
    })
    return {"success": stopped, "message": "تم إيقاف المهمة بنجاح."}


@app.post("/api/run")
async def run_workflow(req: RunRequest, request: Request):
    if crew.is_running:
        raise HTTPException(status_code=409, detail="هناك مهمة قيد التنفيذ حالياً في المكتب. يرجى إيقافها أولاً.")

    # Apply per-user API key if available
    user = get_current_user_from_req(request)
    eff_provider = req.provider
    eff_key = req.api_key
    eff_model = req.model

    if user:
        u_cfg = auth_manager.get_user_llm_config(user["username"])
        if u_cfg.get("api_key") and not eff_key:
            eff_key = u_cfg["api_key"]
            if u_cfg.get("provider"):
                eff_provider = u_cfg["provider"]
            if u_cfg.get("model"):
                eff_model = u_cfg["model"]

    if eff_provider or eff_key or eff_model:
        crew.update_config(
            provider=eff_provider,
            api_key=eff_key,
            model=eff_model
        )

    session_id = req.session_id or "default_session"
    project_id = req.project_id or "default_project"

    # Update file watcher to current project workspace
    try:
        file_watcher.watch_directory(crew.project_manager.get_workspace_dir(project_id))
    except Exception:
        pass

    crew._current_run_task = asyncio.create_task(
        crew.run(
            user_request=req.prompt,
            session_id=session_id,
            project_id=project_id,
            target_agent=req.target_agent or "all"
        )
    )
    return {
        "message": "بدأت المهمة في استوديو الوكلاء بنجاح",
        "session_id": session_id,
        "project_id": project_id,
        "target_agent": req.target_agent,
        "user": user["username"] if user else "admin"
    }


# ============================================================
# Live File Editing & Interactive Terminal Endpoints
# ============================================================

@app.post("/api/projects/{project_id}/files/save")
async def save_file_endpoint(project_id: str, req: SaveFileRequest):
    """Saves modified code directly to disk and broadcasts event."""
    res = await crew.project_manager.save_file_content(project_id, req.path, req.content)
    if res.get("success"):
        await ws_manager.broadcast({
            "event": "file_saved_live",
            "project_id": project_id,
            "path": req.path
        })
    return res


@app.post("/api/projects/{project_id}/terminal/run")
async def run_terminal_command(project_id: str, req: TerminalRunRequest):
    """Executes a terminal shell command inside project workspace."""
    res = await crew.project_manager.execute_terminal_command(project_id, req.command, timeout=req.timeout)
    return res


# ============================================================
# Project Management & Revisions (Version Control) Endpoints
# ============================================================

@app.get("/api/projects")
async def list_projects():
    projects = crew.project_manager.list_all_projects()
    return {"projects": projects, "total": len(projects)}


@app.post("/api/projects")
async def create_new_project(req: CreateProjectRequest):
    res = crew.project_manager.create_project(
        project_id=req.id,
        name=req.name,
        description=req.description
    )
    return res


@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: str):
    return crew.project_manager.delete_project(project_id)


@app.post("/api/projects/{project_id}/open-folder")
async def open_project_folder(project_id: str):
    success = crew.project_manager.open_in_file_explorer(project_id)
    return {"success": success, "message": "تم فتح مجلد المشروع في مستكشف الملفات."}


@app.get("/api/projects/{project_id}/files")
async def get_project_files(project_id: str):
    files = crew.project_manager.list_project_files(project_id)
    return {"project_id": project_id, "files": files, "count": len(files)}


@app.get("/api/projects/{project_id}/revisions")
async def list_project_revisions(project_id: str):
    """Returns the version control commit snapshots for the project."""
    revisions = crew.project_manager.revisions.list_revisions(project_id)
    return {"project_id": project_id, "revisions": revisions, "total": len(revisions)}


@app.post("/api/projects/{project_id}/revisions/{rev_id}/rollback")
async def rollback_project_revision(project_id: str, rev_id: str):
    """Rolls back the workspace to an earlier snapshot."""
    ws_dir = crew.project_manager.get_workspace_dir(project_id)
    res = crew.project_manager.revisions.rollback(project_id, rev_id, ws_dir)
    if res.get("success"):
        await ws_manager.broadcast({
            "event": "revision_restored",
            "project_id": project_id,
            "rev_id": rev_id
        })
    return res


@app.get("/api/projects/{project_id}/download-zip")
async def download_project_zip(project_id: str):
    zip_bytes = crew.project_manager.generate_zip_bytes(project_id)
    filename = f"{project_id}.zip"
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.post("/api/projects/{project_id}/run")
async def run_project_on_server(project_id: str, req: RunServerRequest):
    result = await crew.project_manager.run_server_process(project_id, command=req.command)
    return result


@app.post("/api/projects/{project_id}/stop-process")
async def stop_project_server(project_id: str):
    return crew.project_manager.stop_server_process(project_id)


# ============================================================
# Live Project Preview Endpoints
# ============================================================

def generate_fallback_preview_html(project_id: str, files: List[Dict[str, Any]]) -> str:
    files_list_html = "".join(f"""
        <div style="background:#111a30; border:1px solid #1e293b; border-radius:12px; padding:12px; margin-bottom:12px;">
            <div style="color:#38bdf8; font-weight:bold; font-family:monospace; margin-bottom:6px; display:flex; justify-content:space-between;">
                <span>📄 {f['path']}</span>
                <span style="color:#64748b; font-size:11px;">{f['size']} B</span>
            </div>
            <pre style="background:#070b14; color:#94a3b8; padding:12px; border-radius:8px; font-size:12px; max-height:220px; overflow-y:auto; margin:0; white-space:pre-wrap; font-family:monospace;">{f['content'][:1500] + ('...' if len(f['content']) > 1500 else '')}</pre>
        </div>
    """ for f in files[:8])
    
    return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>Live Preview - {project_id}</title>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body {{ background:#070b14; color:#f8fafc; font-family:'Cairo',sans-serif; margin:0; padding:24px; }}
        .header {{ background:#0c1322; border:1px solid rgba(56,189,248,0.25); border-radius:16px; padding:20px; margin-bottom:20px; box-shadow:0 10px 30px rgba(0,0,0,0.5); }}
        .badge {{ background:rgba(16,185,129,0.15); color:#10b981; border:1px solid rgba(16,185,129,0.3); padding:4px 14px; border-radius:20px; font-size:12px; font-weight:bold; display:inline-block; }}
    </style>
</head>
<body>
    <div class="header">
        <div class="badge">● معاينة حية للمشروع (Live Project Sandbox)</div>
        <h2 style="margin:10px 0 6px 0; color:#38bdf8;">مشروع: {project_id}</h2>
        <p style="color:#94a3b8; font-size:13px; margin:0;">تم بناء وتجهيز {len(files)} ملفات في بيئة العمل. عند بناء تطبيق ويب، ستظهر واجهة المستخدم تلقائياً هنا في هذه المعاينة المباشرة.</p>
    </div>
    <div>
        <h3 style="color:#cbd5e1; font-size:14px; margin-bottom:12px;">📂 ملفات المشروع الجاهزة:</h3>
        {files_list_html if files else '<div style="color:#64748b; padding:20px; text-align:center;">لا توجد ملفات في المشروع حتى الآن.</div>'}
    </div>
</body>
</html>"""


@app.get("/api/projects/{project_id}/preview")
async def project_preview_index(project_id: str):
    ws = crew.project_manager.get_workspace_dir(project_id)
    if not ws.exists():
        raise HTTPException(status_code=404, detail="المشروع غير موجود")
    
    candidates = [
        ws / "index.html",
        ws / "static" / "index.html",
        ws / "public" / "index.html",
        ws / "dist" / "index.html"
    ]
    for c in candidates:
        if c.exists() and c.is_file():
            return FileResponse(str(c))
    
    files = crew.project_manager.list_project_files(project_id)
    html_content = generate_fallback_preview_html(project_id, files)
    return Response(content=html_content, media_type="text/html")


@app.get("/api/projects/{project_id}/preview/{subpath:path}")
async def project_preview_assets(project_id: str, subpath: str):
    ws = crew.project_manager.get_workspace_dir(project_id)
    safe_path = (ws / subpath).resolve()
    
    if not str(safe_path).startswith(str(ws.resolve())):
        raise HTTPException(status_code=403, detail="Forbidden")
    
    if safe_path.exists() and safe_path.is_file():
        return FileResponse(str(safe_path))
    
    static_sub = (ws / "static" / subpath).resolve()
    if static_sub.exists() and static_sub.is_file():
        return FileResponse(str(static_sub))
        
    raise HTTPException(status_code=404, detail="الملف غير موجود")


@app.get("/api/projects/{project_id}/preview-status")
async def get_preview_status(project_id: str):
    ws = crew.project_manager.get_workspace_dir(project_id)
    has_html = any((ws / name).exists() for name in ["index.html", "static/index.html", "public/index.html", "dist/index.html"])
    process = crew.project_manager.running_processes.get(project_id)
    is_server_running = bool(process and process.returncode is None)
    pid = process.pid if is_server_running else None
    
    return {
        "project_id": project_id,
        "has_html_entry": has_html,
        "is_server_running": is_server_running,
        "server_pid": pid,
        "preview_url": f"/api/projects/{project_id}/preview"
    }


# ============================================================
# Cloud & Desktop Bi-Directional Synchronization Endpoints
# ============================================================

@app.get("/api/projects/{project_id}/manifest")
async def get_project_manifest(project_id: str):
    return crew.project_manager.sync_engine.get_manifest(project_id)


@app.post("/api/projects/{project_id}/sync/batch-upload")
async def sync_batch_upload(project_id: str, req: BatchUploadRequest):
    written = crew.project_manager.batch_write_files(project_id, req.files)
    await ws_manager.broadcast({
        "event": "cloud_sync_update",
        "project_id": project_id,
        "files_updated": written,
        "message": f"تم استلام وتحديث {written} ملف سحابياً بنجاح."
    })
    return {"success": True, "written_count": written}


@app.post("/api/projects/{project_id}/sync/push")
async def sync_push(project_id: str, req: SyncRequest):
    res = await crew.project_manager.sync_engine.push_to_remote(
        remote_url=req.remote_url,
        project_id=project_id,
        auth_token=req.auth_token
    )
    return res


@app.post("/api/projects/{project_id}/sync/pull")
async def sync_pull(project_id: str, req: SyncRequest):
    res = await crew.project_manager.sync_engine.pull_from_remote(
        remote_url=req.remote_url,
        project_id=project_id,
        auth_token=req.auth_token
    )
    return res


@app.post("/api/projects/{project_id}/sync/two-way")
async def sync_two_way(project_id: str, req: SyncRequest):
    res = await crew.project_manager.sync_engine.sync_bidirectional(
        remote_url=req.remote_url,
        project_id=project_id,
        auth_token=req.auth_token
    )
    return res


# ============================================================
# Multi-Turn Session Memory Endpoints
# ============================================================

@app.get("/api/sessions/{session_id}")
async def get_session_history(session_id: str):
    return crew.memory.get_or_create_session(session_id)


@app.post("/api/sessions/{session_id}/clear")
async def clear_session(session_id: str):
    session = crew.memory.get_or_create_session(session_id)
    session["history"] = []
    session["context_summary"] = ""
    session["last_deliverables"] = {}
    crew.memory._save()
    return {"success": True, "message": "تمت إعادة ضبط سياق المحادثة."}


# ============================================================
# WebSockets Endpoint
# ============================================================

@app.websocket("/ws/agents")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    await websocket.send_json({
        "event": "connected",
        "provider": crew.llm.provider,
        "model": crew.llm.model,
        "agents": list(crew.agents_state.values()),
        "projects": crew.project_manager.list_all_projects()
    })
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
