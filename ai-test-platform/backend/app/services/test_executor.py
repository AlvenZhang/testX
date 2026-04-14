"""测试执行引擎 - Docker 沙箱"""
import docker
import uuid
import asyncio
from datetime import datetime
from typing import Optional
import httpx

from ..core.config import get_settings


class TestExecutor:
    """测试执行引擎"""

    def __init__(self):
        settings = get_settings()
        self.docker_client = docker.from_env()
        self.sandbox_image = settings.sandbox_image or "ai-test-sandbox:latest"
        self.network_name = "aitest-network"
        self._ensure_network()

    def _ensure_network(self):
        """确保 Docker 网络存在"""
        try:
            self.docker_client.networks.get(self.network_name)
        except docker.errors.NotFound:
            self.docker_client.networks.create(self.network_name, driver="bridge")

    async def execute_test(
        self,
        run_id: str,
        code_content: str,
        test_type: str = "web",
        framework: str = "pytest"
    ) -> dict:
        """
        执行测试

        Args:
            run_id: 测试运行ID
            code_content: 测试代码内容
            test_type: 测试类型 (web/api)
            framework: 测试框架 (pytest)

        Returns:
            执行结果字典
        """
        container = None
        try:
            # 1. 创建测试目录
            test_dir = f"/tmp/test-run-{run_id}"
            test_file = f"{test_dir}/test_sample.py"

            # 2. 写入测试代码
            import os
            os.makedirs(test_dir, exist_ok=True)
            with open(test_file, "w") as f:
                f.write(code_content)

            # 3. 创建沙箱容器
            container = await self._create_sandbox(run_id)

            # 4. 复制测试代码到容器
            await self._copy_code(container, test_dir, "/app")

            # 5. 执行测试
            result = await self._run_tests(container, framework)

            # 6. 获取日志
            logs = await self._get_logs(container)

            return {
                "status": "success" if result["exit_code"] == 0 else "failed",
                "exit_code": result["exit_code"],
                "logs": logs,
                "duration_ms": result.get("duration_ms", 0),
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "logs": "",
            }
        finally:
            if container:
                await self._destroy_sandbox(container)

    async def _create_sandbox(self, run_id: str):
        """创建 Docker 沙箱容器"""
        container = self.docker_client.containers.run(
            self.sandbox_image,
            detach=True,
            mem_limit="1g",
            cpu_period=100000,
            cpu_quota=200000,
            hostname=f"test-run-{run_id}",
            network=self.network_name,
            remove=False,
            command="sleep infinity"
        )
        # 等待容器启动
        await asyncio.sleep(1)
        return container

    async def _copy_code(self, container, src_dir: str, dest_dir: str):
        """复制测试代码到容器"""
        import tarfile
        import io

        # 创建 tar 包
        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode='w') as tar:
            for filename in ["test_sample.py"]:
                filepath = f"{src_dir}/{filename}"
                if os.path.exists(filepath):
                    tar.add(filepath, arcname=filename)
        tar_stream.seek(0)

        # 复制到容器
        container.put_archive(dest_dir, tar_stream)

    async def _run_tests(self, container, framework: str = "pytest") -> dict:
        """执行测试"""
        start_time = datetime.now()

        # 在容器中执行 pytest
        exec_result = container.exec_run(
            f"python -m pytest /app/test_sample.py -v --tb=short",
            socket=True,
            stream=True
        )

        logs = []
        exit_code = 0

        # 读取输出流
        import socket
        sock = exec_result.output
        if hasattr(sock, 'recv'):
            # socket 模式
            while True:
                try:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    logs.append(chunk.decode('utf-8', errors='ignore'))
                except socket.timeout:
                    break
        else:
            # bytes 模式
            for chunk in exec_result.output:
                if isinstance(chunk, bytes):
                    logs.append(chunk.decode('utf-8', errors='ignore'))
                else:
                    logs.append(str(chunk))

        exit_code = exec_result.exit_code

        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        return {
            "exit_code": exit_code,
            "logs": "".join(logs),
            "duration_ms": duration_ms
        }

    async def _get_logs(self, container) -> str:
        """获取容器日志"""
        try:
            logs = container.logs(stdout=True, stderr=True, tail=100).decode('utf-8', errors='ignore')
            return logs
        except Exception:
            return ""

    async def _destroy_sandbox(self, container):
        """销毁沙箱容器"""
        try:
            container.stop(timeout=5)
            container.remove(force=True)
        except Exception:
            pass


# 全局单例
_executor: Optional[TestExecutor] = None


def get_test_executor() -> TestExecutor:
    """获取测试执行器实例"""
    global _executor
    if _executor is None:
        _executor = TestExecutor()
    return _executor
