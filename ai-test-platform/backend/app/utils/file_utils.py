"""文件处理工具"""
import os
import shutil
from pathlib import Path
from typing import Optional


def ensure_dir(path: str) -> str:
    """
    确保目录存在，不存在则创建

    Args:
        path: 目录路径

    Returns:
        目录路径
    """
    Path(path).mkdir(parents=True, exist_ok=True)
    return path


def read_file(path: str, encoding: str = "utf-8") -> str:
    """
    读取文件内容

    Args:
        path: 文件路径
        encoding: 编码格式

    Returns:
        文件内容
    """
    with open(path, "r", encoding=encoding) as f:
        return f.read()


def write_file(path: str, content: str, encoding: str = "utf-8") -> bool:
    """
    写入文件内容

    Args:
        path: 文件路径
        content: 文件内容
        encoding: 编码格式

    Returns:
        是否成功
    """
    try:
        ensure_dir(os.path.dirname(path))
        with open(path, "w", encoding=encoding) as f:
            f.write(content)
        return True
    except Exception:
        return False


def copy_file(src: str, dst: str) -> bool:
    """
    复制文件

    Args:
        src: 源文件路径
        dst: 目标文件路径

    Returns:
        是否成功
    """
    try:
        ensure_dir(os.path.dirname(dst))
        shutil.copy2(src, dst)
        return True
    except Exception:
        return False


def get_file_extension(path: str) -> str:
    """获取文件扩展名"""
    return os.path.splitext(path)[1].lower()


def get_file_size(path: str) -> int:
    """获取文件大小（字节）"""
    return os.path.getsize(path)


def list_files(directory: str, pattern: str = "*", recursive: bool = False) -> list[str]:
    """
    列出目录下的文件

    Args:
        directory: 目录路径
        pattern: 文件名模式
        recursive: 是否递归

    Returns:
        文件路径列表
    """
    path = Path(directory)
    if recursive:
        return [str(f) for f in path.rglob(pattern) if f.is_file()]
    else:
        return [str(f) for f in path.glob(pattern) if f.is_file()]


def delete_file(path: str) -> bool:
    """删除文件"""
    try:
        if os.path.exists(path):
            os.remove(path)
        return True
    except Exception:
        return False


def create_temp_file(suffix: str = "", prefix: str = "tmp") -> str:
    """创建临时文件"""
    import tempfile
    fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
    os.close(fd)
    return path


def read_json_lines(path: str) -> list:
    """读取 JSON Lines 格式文件"""
    result = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                import json
                result.append(json.loads(line))
    return result
