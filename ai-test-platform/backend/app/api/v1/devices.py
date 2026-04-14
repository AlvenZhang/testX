"""设备管理 API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid
import base64

from ...core.database import get_db
from ...models.device import Device
from ...services.device_service import get_device_service

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("/")
async def list_devices(
    platform: str = None,
    db: AsyncSession = Depends(get_db)
):
    """获取设备列表"""
    query = select(Device)
    if platform:
        query = query.where(Device.platform == platform)
    result = await db.execute(query)
    devices = result.scalars().all()
    return [
        {
            "id": d.id,
            "name": d.name,
            "platform": d.platform,
            "device_type": d.device_type,
            "serial": d.serial,
            "status": d.status,
            "os_version": d.os_version,
            "manufacturer": d.manufacturer,
            "model": d.model,
        }
        for d in devices
    ]


@router.post("/discover")
async def discover_devices(
    platform: str = "android",
    db: AsyncSession = Depends(get_db)
):
    """发现新设备"""
    device_service = get_device_service()

    if platform == "android":
        discovered = await device_service.discover_android_devices()
    elif platform == "ios":
        discovered = await device_service.discover_ios_devices()
    else:
        raise HTTPException(status_code=400, detail="Invalid platform")

    # 保存发现的设备到数据库
    saved_devices = []
    for dev in discovered:
        # 检查是否已存在
        result = await db.execute(
            select(Device).where(Device.serial == dev.get("serial"))
        )
        existing = result.scalar_one_or_none()

        if existing:
            # 更新状态
            existing.status = dev.get("status", "online")
            await db.commit()
            saved_devices.append(existing)
        else:
            # 创建新设备
            device = Device(
                id=str(uuid.uuid4()),
                name=dev.get("name") or dev.get("model") or dev.get("serial", "Unknown"),
                platform=platform,
                device_type=dev.get("device_type", "real_device"),
                serial=dev.get("serial", ""),
                status=dev.get("status", "online"),
                os_version=dev.get("os_version"),
                manufacturer=dev.get("manufacturer"),
                model=dev.get("model"),
                capabilities={},
            )
            db.add(device)
            await db.commit()
            await db.refresh(device)
            saved_devices.append(device)

    return {
        "discovered_count": len(discovered),
        "saved_count": len(saved_devices),
        "devices": saved_devices,
    }


@router.get("/{device_id}/screenshot")
async def get_device_screenshot(
    device_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取设备截图"""
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    device_service = get_device_service()
    screenshot = await device_service.get_device_screenshot(device.serial, device.platform)

    if screenshot:
        return {
            "device_id": device_id,
            "screenshot": base64.b64encode(screenshot).decode("utf-8"),
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to capture screenshot")


@router.delete("/{device_id}")
async def delete_device(device_id: str, db: AsyncSession = Depends(get_db)):
    """删除设备"""
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    await db.delete(device)
    await db.commit()
