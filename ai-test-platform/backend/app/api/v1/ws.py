"""WebSocket 实时日志"""
from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import json
from typing import Dict

# 存储活跃的 WebSocket 连接
active_connections: Dict[str, WebSocket] = {}


async def websocket_endpoint(websocket: WebSocket, run_id: str):
    """WebSocket 端点用于实时测试日志推送"""
    await websocket.accept()
    active_connections[run_id] = websocket
    try:
        while True:
            # 保持连接，等待消息
            data = await websocket.receive_text()
            # 可以处理心跳等消息
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        if run_id in active_connections:
            del active_connections[run_id]


async def send_log(run_id: str, log_message: str):
    """发送日志到指定测试运行的 WebSocket 连接"""
    if run_id in active_connections:
        try:
            await active_connections[run_id].send_text(json.dumps({
                "type": "log",
                "message": log_message
            }))
        except Exception:
            pass


async def send_status(run_id: str, status: str):
    """发送状态更新到 WebSocket"""
    if run_id in active_connections:
        try:
            await active_connections[run_id].send_text(json.dumps({
                "type": "status",
                "status": status
            }))
        except Exception:
            pass
