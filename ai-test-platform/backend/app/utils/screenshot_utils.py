"""截图处理工具"""
import base64
import os
from datetime import datetime
from io import BytesIO
from typing import Optional, Tuple


def compress_image(
    image_data: bytes,
    quality: int = 85,
    max_width: int = 1920,
    max_height: int = 1080
) -> bytes:
    """
    压缩图片

    Args:
        image_data: 原始图片数据
        quality: JPEG 质量 (1-100)
        max_width: 最大宽度
        max_height: 最大高度

    Returns:
        压缩后的图片数据
    """
    try:
        from PIL import Image
        import io

        img = Image.open(BytesIO(image_data))

        # 转换为 RGB（如果是 RGBA）
        if img.mode == "RGBA":
            rgb = Image.new("RGB", img.size, (255, 255, 255))
            rgb.paste(img, mask=img.split()[3])
            img = rgb

        # 缩放
        width, height = img.size
        if width > max_width or height > max_height:
            ratio = min(max_width / width, max_height / height)
            new_size = (int(width * ratio), int(height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        # 保存为 JPEG
        output = BytesIO()
        img.save(output, format="JPEG", quality=quality, optimize=True)
        return output.getvalue()
    except ImportError:
        # 如果没有 PIL，直接返回原数据
        return image_data


def validate_image(image_data: bytes, max_size_mb: float = 10.0) -> Tuple[bool, Optional[str]]:
    """
    验证图片数据

    Args:
        image_data: 图片数据
        max_size_mb: 最大文件大小（MB）

    Returns:
        (是否有效, 错误信息)
    """
    # 检查大小
    size_mb = len(image_data) / (1024 * 1024)
    if size_mb > max_size_mb:
        return False, f"Image size {size_mb:.2f}MB exceeds maximum {max_size_mb}MB"

    # 检查格式
    try:
        from PIL import Image
        img = Image.open(BytesIO(image_data))
        img.verify()
        return True, None
    except ImportError:
        # 如果没有 PIL，只做基本检查
        if image_data[:3] == b"\xff\xd8\xff":  # JPEG
            return True, None
        if image_data[:8] == b"\x89PNG\r\n\x1a\n":  # PNG
            return True, None
        return False, "Unsupported image format"
    except Exception as e:
        return False, f"Invalid image: {str(e)}"


def base64_to_image(base64_str: str) -> bytes:
    """
    Base64 字符串转换为图片数据

    Args:
        base64_str: Base64 编码的图片字符串

    Returns:
        图片数据
    """
    # 移除 data URI 前缀
    if "," in base64_str:
        base64_str = base64_str.split(",")[1]

    return base64.b64decode(base64_str)


def image_to_base64(image_data: bytes, format: str = "PNG") -> str:
    """
    图片数据转换为 Base64 字符串

    Args:
        image_data: 图片数据
        format: 图片格式

    Returns:
        Base64 编码的字符串
    """
    return f"data:image/{format.lower()};base64,{base64.b64encode(image_data).decode()}"


def generate_screenshot_filename(prefix: str = "screenshot", extension: str = "png") -> str:
    """
    生成截图文件名

    Args:
        prefix: 文件名前缀
        extension: 文件扩展名

    Returns:
        文件名
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.{extension}"


def save_screenshot(image_data: bytes, output_dir: str, prefix: str = "screenshot") -> Optional[str]:
    """
    保存截图

    Args:
        image_data: 图片数据
        output_dir: 输出目录
        prefix: 文件名前缀

    Returns:
        保存的文件路径
    """
    from .file_utils import ensure_dir

    try:
        ensure_dir(output_dir)
        filename = generate_screenshot_filename(prefix)
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "wb") as f:
            f.write(image_data)

        return filepath
    except Exception:
        return None
