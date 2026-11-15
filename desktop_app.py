import sys
import time
import threading
import urllib.request
import argparse
import ssl
from pathlib import Path
import os

# Ensure UTF-8 on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import uvicorn
import webview
import config
from core.project_manager import ProjectManager

HOST = config.HOST
PORT = config.PORT
LOCAL_HOST = "127.0.0.1" if HOST in ("0.0.0.0", "") else HOST
LOCAL_SERVER_URL = f"http://{LOCAL_HOST}:{PORT}"
DEFAULT_CLOUD_URL = os.getenv("CLOUD_URL", "")

pm = ProjectManager()

class DesktopBridgeApi:
    """Native Python API callable directly from the Web UI inside Desktop App"""
    def __init__(self, target_url: str):
        self.target_url = target_url

    def open_folder(self, project_id: str = "default_project") -> bool:
        return pm.open_in_file_explorer(project_id)

    def is_desktop(self) -> bool:
        return True

    def get_info(self) -> dict:
        return {
            "platform": sys.platform,
            "version": "3.0.0-Desktop-CloudLinked",
            "is_desktop": True,
            "connected_url": self.target_url,
            "cloud_url": DEFAULT_CLOUD_URL,
            "local_url": LOCAL_SERVER_URL,
            "workspace_root": str(pm.base_dir.resolve())
        }

    def sync_with_cloud(self, project_id: str = "default_project") -> dict:
        import asyncio
        from core.sync_engine import ProjectSyncEngine
        engine = ProjectSyncEngine(pm.base_dir)
        try:
            res = asyncio.run(engine.sync_bidirectional(DEFAULT_CLOUD_URL, project_id))
            return res
        except Exception as e:
            return {"success": False, "error": str(e)}

def is_url_reachable(url: str, timeout: float = 2.5) -> bool:
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(
            f"{url.rstrip('/')}/api/status",
            headers={"User-Agent": "PriceZ-Desktop/3.0"}
        )
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return resp.status == 200
    except Exception:
        return False

def start_local_server():
    if is_url_reachable(LOCAL_SERVER_URL, timeout=1.0):
        print(f"[*] Local server is already running at {LOCAL_SERVER_URL}")
        return

    def run_uvicorn():
        print(f"[*] Starting local background server on {LOCAL_SERVER_URL}...")
        uvicorn.run("api.server:app", host=HOST, port=PORT, log_level="warning")

    server_thread = threading.Thread(target=run_uvicorn, daemon=True)
    server_thread.start()

    retries = 20
    while retries > 0 and not is_url_reachable(LOCAL_SERVER_URL, timeout=0.5):
        time.sleep(0.3)
        retries -= 1

    if is_url_reachable(LOCAL_SERVER_URL, timeout=0.5):
        print("[+] Local server started successfully.")
    else:
        print("[!] Local server startup timed out.")

def main():
    parser = argparse.ArgumentParser(description="PriceZ Agents 3D Office - Desktop Edition")
    parser.add_argument("--local", action="store_true", help="Force connecting to local offline server")
    parser.add_argument("--url", type=str, default=None, help="Custom server URL to connect to")
    parser.add_argument("--sync", action="store_true", help="Perform bidirectional sync with cloud before opening")
    args = parser.parse_args()

    print("=" * 65)
    print("👑 Launching PriceZ Agents 3D Virtual AI Office (Desktop Edition)")
    print("=" * 65)

    target_url = None

    if args.url:
        target_url = args.url
    elif args.local:
        start_local_server()
        target_url = LOCAL_SERVER_URL
    else:
        # Check cloud server availability if configured
        if DEFAULT_CLOUD_URL and is_url_reachable(DEFAULT_CLOUD_URL, timeout=3.0):
            print(f"[✓] Cloud Server is ONLINE at {DEFAULT_CLOUD_URL}")
            target_url = DEFAULT_CLOUD_URL
            threading.Thread(target=start_local_server, daemon=True).start()
        else:
            start_local_server()
            target_url = LOCAL_SERVER_URL

    if args.sync and DEFAULT_CLOUD_URL:
        print(f"[*] Performing pre-launch sync with {DEFAULT_CLOUD_URL}...")
        import asyncio
        from core.sync_engine import ProjectSyncEngine
        engine = ProjectSyncEngine(pm.base_dir)
        try:
            res = asyncio.run(engine.sync_bidirectional(DEFAULT_CLOUD_URL, "default_project"))
            print(f"[✓] Sync Result: {res.get('message')}")
        except Exception as e:
            print(f"[!] Sync error: {e}")

    print(f"🚀 Opening Desktop Window connected to: {target_url}")

    is_cloud = bool(target_url and "localhost" not in target_url and "127.0.0.1" not in target_url)
    title_suffix = "السحابية (Cloud)" if is_cloud else "المحلية (Localhost)"

    bridge = DesktopBridgeApi(target_url)
    window = webview.create_window(
        title=f"PriceZ Agents - AI 3D Office - النسخة {title_suffix}",
        url=target_url,
        width=1440,
        height=900,
        min_size=(1100, 720),
        js_api=bridge,
        text_select=True
    )

    webview.start(debug=False)

if __name__ == "__main__":
    main()
