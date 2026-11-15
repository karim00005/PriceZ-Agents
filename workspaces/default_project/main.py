import asyncio
from datetime import datetime
from models import AttendanceLog, SystemConfig

class ZKBridgedDevice:
    def __init__(self, config: SystemConfig):
        self.config = config
        self.connected = False

    async def connect(self):
        print(f"[Device] Connecting to {self.config.device_ip}:{self.config.port}...")
        await asyncio.sleep(0.2)
        self.connected = True
        print("[Device] Connected successfully.")

    async def fetch_logs(self):
        if not self.connected:
            await self.connect()
        return [
            AttendanceLog(user_id="EMP-101", timestamp=datetime.now(), punch_type="Fingerprint"),
            AttendanceLog(user_id="EMP-102", timestamp=datetime.now(), punch_type="FaceRecognition"),
        ]

if __name__ == "__main__":
    async def run():
        dev = ZKBridgedDevice(SystemConfig())
        logs = await dev.fetch_logs()
        print(f"Total retrieved logs: {len(logs)}")
        for l in logs:
            print(f"  -> {l.user_id} at {l.timestamp}")
    asyncio.run(run())
