"""沙箱执行器公共工具函数"""
import os
import json
import logging
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


def setup_logging(log_level: str = "INFO") -> None:
    """设置日志配置"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="[%(asctime)s] %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def run_command(
    cmd: List[str],
    cwd: Optional[str] = None,
    timeout: int = 300,
    env: Optional[Dict[str, str]] = None,
) -> subprocess.CompletedProcess:
    """
    运行命令

    Args:
        cmd: 命令列表
        cwd: 工作目录
        timeout: 超时时间（秒）
        env: 环境变量

    Returns:
        CompletedProcess对象
    """
    full_env = os.environ.copy()
    if env:
        full_env.update(env)

    logger.info(f"Running command: {' '.join(cmd)}")

    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=full_env,
    )

    if result.returncode != 0:
        logger.error(f"Command failed with exit code {result.returncode}")
        logger.error(f"stdout: {result.stdout}")
        logger.error(f"stderr: {result.stderr}")

    return result


async def run_command_async(
    cmd: List[str],
    cwd: Optional[str] = None,
    timeout: int = 300,
    env: Optional[Dict[str, str]] = None,
) -> subprocess.CompletedProcess:
    """
    异步运行命令

    Args:
        cmd: 命令列表
        cwd: 工作目录
        timeout: 超时时间（秒）
        env: 环境变量

    Returns:
        CompletedProcess对象
    """
    import asyncio

    full_env = os.environ.copy()
    if env:
        full_env.update(env)

    logger.info(f"Running async command: {' '.join(cmd)}")

    process = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=cwd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=full_env,
    )

    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout,
        )
        result = subprocess.CompletedProcess(
            args=cmd,
            returncode=process.returncode,
            stdout=stdout.decode() if stdout else "",
            stderr=stderr.decode() if stderr else "",
        )

        if result.returncode != 0:
            logger.error(f"Command failed with exit code {result.returncode}")

        return result

    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
        raise TimeoutError(f"Command timed out after {timeout} seconds")


def parse_junit_xml(xml_content: str) -> Dict[str, Any]:
    """
    解析JUnit XML测试报告

    Args:
        xml_content: XML内容

    Returns:
        解析后的测试结果
    """
    try:
        import xml.etree.ElementTree as ET

        root = ET.fromstring(xml_content)

        result = {
            "tests": 0,
            "failures": 0,
            "errors": 0,
            "skipped": 0,
            "time": 0.0,
            "test_cases": [],
        }

        if hasattr(root, "attrib"):
            result["tests"] = int(root.attrib.get("tests", 0))
            result["failures"] = int(root.attrib.get("failures", 0))
            result["errors"] = int(root.attrib.get("errors", 0))
            result["skipped"] = int(root.attrib.get("skipped", 0))
            result["time"] = float(root.attrib.get("time", 0))

        for testcase in root.findall(".//testcase"):
            tc_result = {
                "classname": testcase.attrib.get("classname", ""),
                "name": testcase.attrib.get("name", ""),
                "time": float(testcase.attrib.get("time", 0)),
                "status": "passed",
                "message": "",
            }

            failure = testcase.find("failure")
            if failure is not None:
                tc_result["status"] = "failed"
                tc_result["message"] = failure.attrib.get("message", "")

            error = testcase.find("error")
            if error is not None:
                tc_result["status"] = "error"
                tc_result["message"] = error.attrib.get("message", "")

            skipped = testcase.find("skipped")
            if skipped is not None:
                tc_result["status"] = "skipped"

            result["test_cases"].append(tc_result)

        return result

    except Exception as e:
        logger.error(f"Failed to parse JUnit XML: {e}")
        return {
            "tests": 0,
            "failures": 0,
            "errors": 0,
            "skipped": 0,
            "time": 0.0,
            "test_cases": [],
            "parse_error": str(e),
        }


def ensure_directory(path: str) -> Path:
    """
    确保目录存在

    Args:
        path: 目录路径

    Returns:
        Path对象
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def save_test_results(
    results: Dict[str, Any],
    output_dir: str,
    run_id: str,
) -> str:
    """
    保存测试结果

    Args:
        results: 测试结果
        output_dir: 输出目录
        run_id: 执行ID

    Returns:
        结果文件路径
    """
    ensure_directory(output_dir)

    result_file = Path(output_dir) / f"{run_id}_results.json"

    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info(f"Test results saved to {result_file}")
    return str(result_file)


def load_json_file(file_path: str) -> Optional[Dict[str, Any]]:
    """
    加载JSON文件

    Args:
        file_path: 文件路径

    Returns:
        JSON数据或None
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load JSON file {file_path}: {e}")
        return None


def save_json_file(data: Dict[str, Any], file_path: str) -> bool:
    """
    保存JSON文件

    Args:
        data: 数据
        file_path: 文件路径

    Returns:
        是否成功
    """
    try:
        ensure_directory(str(Path(file_path).parent))
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Failed to save JSON file {file_path}: {e}")
        return False


def get_file_hash(file_path: str, algorithm: str = "md5") -> Optional[str]:
    """
    计算文件哈希值

    Args:
        file_path: 文件路径
        algorithm: 算法 (md5, sha1, sha256)

    Returns:
        哈希值字符串
    """
    import hashlib

    try:
        hash_obj = hashlib.new(algorithm)
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except Exception as e:
        logger.error(f"Failed to compute hash for {file_path}: {e}")
        return None


def cleanup_old_files(directory: str, max_age_hours: int = 24) -> int:
    """
    清理旧文件

    Args:
        directory: 目录路径
        max_age_hours: 最大保留时间（小时）

    Returns:
        清理的文件数量
    """
    import time

    dir_path = Path(directory)
    if not dir_path.exists():
        return 0

    cutoff_time = time.time() - (max_age_hours * 3600)
    removed_count = 0

    for file_path in dir_path.rglob("*"):
        if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
            try:
                file_path.unlink()
                removed_count += 1
                logger.info(f"Removed old file: {file_path}")
            except Exception as e:
                logger.error(f"Failed to remove {file_path}: {e}")

    return removed_count
