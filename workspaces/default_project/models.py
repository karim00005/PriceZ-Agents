from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class AttendanceLog(BaseModel):
    user_id: str = Field(..., description="Employee User ID")
    timestamp: datetime = Field(..., description="Punch datetime")
    punch_type: str = Field(default="Fingerprint")

class SystemConfig(BaseModel):
    device_ip: str = "192.168.1.201"
    port: int = 4370
    timeout: float = 5.0
