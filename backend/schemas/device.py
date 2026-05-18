from pydantic import BaseModel, ConfigDict

class DeviceBase(BaseModel):
    name: str | None = None
    serial: str
    platform: str = "android"
    status: str = "online"
    adb_info: dict | None = None

class DeviceCreate(DeviceBase):
    pass

class DeviceUpdate(BaseModel):
    name: str | None = None
    status: str | None = None

class DeviceResponse(DeviceBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
