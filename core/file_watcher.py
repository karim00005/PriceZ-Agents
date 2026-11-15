import asyncio
from pathlib import Path
from typing import Callable, Any, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class WorkspaceChangeHandler(FileSystemEventHandler):
    def __init__(self, callback: Callable[[str, str], Any], loop: asyncio.AbstractEventLoop):
        super().__init__()
        self.callback = callback
        self.loop = loop

    def on_any_event(self, event):
        if event.is_directory or "__pycache__" in event.src_path or ".git" in event.src_path:
            return
        # Fire async callback into event loop
        rel = Path(event.src_path).name
        asyncio.run_coroutine_threadsafe(
            self.callback(event.event_type, rel),
            self.loop
        )

class WorkspaceWatcher:
    def __init__(self, async_event_broadcaster: Callable[[dict], Any]):
        self.broadcaster = async_event_broadcaster
        self.observer = None
        self.current_watched_path: Optional[Path] = None

    async def _on_file_event(self, event_type: str, file_name: str):
        await self.broadcaster({
            "event": "workspace_file_changed",
            "change_type": event_type,
            "filename": file_name
        })

    def watch_directory(self, path: Path):
        self.stop()
        self.current_watched_path = path
        loop = asyncio.get_event_loop()
        handler = WorkspaceChangeHandler(self._on_file_event, loop)
        self.observer = Observer()
        self.observer.schedule(handler, str(path), recursive=True)
        self.observer.daemon = True
        self.observer.start()

    def stop(self):
        if self.observer and self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
            self.observer = None
