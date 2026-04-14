from sqlalchemy import Column, String, Text, JSON, DateTime, Enum, ForeignKey, Integer
from sqlalchemy.sql import func
from ..core.database import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    platform = Column(Enum("android", "ios", name="platform_enum"), nullable=False)
    device_type = Column(Enum("real_device", "emulator", "simulator", name="device_type_enum"), nullable=False)
    serial = Column(String(100))  # ADB serial / iOS uuid
    appium_port = Column(Integer)
    wda_port = Column(Integer)  # iOS WDA port
    status = Column(Enum("online", "offline", "busy", "maintaining", name="device_status_enum"), default="offline")
    os_version = Column(String(20))
    manufacturer = Column(String(50))
    model = Column(String(50))
    capabilities = Column(JSON)  # Appium capabilities
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
