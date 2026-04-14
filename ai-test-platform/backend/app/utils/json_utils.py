"""JSON 序列化工具"""
import json
from datetime import datetime, date
from typing import Any, Optional
from decimal import Decimal


class DateTimeEncoder(json.JSONEncoder):
    """支持 datetime 和 Decimal 的 JSON 编码器"""

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, date):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def safe_json_dumps(obj: Any, **kwargs) -> str:
    """
    安全地序列化对象为 JSON 字符串

    Args:
        obj: 要序列化的对象
        **kwargs: json.dumps 参数

    Returns:
        JSON 字符串
    """
    kwargs.setdefault("ensure_ascii", False)
    kwargs.setdefault("cls", DateTimeEncoder)
    return json.dumps(obj, **kwargs)


def safe_json_loads(text: str, default: Any = None) -> Any:
    """
    安全地解析 JSON 字符串

    Args:
        text: JSON 字符串
        default: 解析失败时的默认值

    Returns:
        解析后的对象
    """
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default


def merge_json(base: dict, override: dict) -> dict:
    """
    合并两个字典，override 优先

    Args:
        base: 基础字典
        override: 覆盖字典

    Returns:
        合并后的字典
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_json(result[key], value)
        else:
            result[key] = value
    return result


def flatten_json(data: dict, parent_key: str = "", sep: str = ".") -> dict:
    """
    扁平化 JSON 对象

    Args:
        data: JSON 对象
        parent_key: 父级键名
        sep: 分隔符

    Returns:
        扁平化后的字典
    """
    items = []
    for k, v in data.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_json(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def unflatten_json(data: dict, sep: str = ".") -> dict:
    """
    反扁平化 JSON 对象

    Args:
        data: 扁平化的字典
        sep: 分隔符

    Returns:
        嵌套字典
    """
    result = {}
    for key, value in data.items():
        parts = key.split(sep)
        current = result
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value
    return result
