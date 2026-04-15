"""测试执行引擎 - Docker 沙箱"""
import asyncio
import json
import os
import tarfile
import uuid
from datetime import datetime
from typing import Optional

import docker
import httpx

from ..core.config import get_settings


class TestExecutor:
    """测试执行引擎 - Docker 沙箱"""

    def __init__(self):
        settings = get_settings()
        self.docker_client = docker.from_env()
        self.sandbox_image = settings.sandbox_image or "ai-test-sandbox:latest"
        self.network_name = "aitest-network"
        self.registry_url = settings.registry_url or ""
        self._ensure_network()

    def _ensure_network(self):
        """确保 Docker 网络存在"""
        try:
            self.docker_client.networks.get(self.network_name)
        except docker.errors.NotFound:
            self.docker_client.networks.create(self.network_name, driver="bridge")

    def _ensure_image(self):
        """确保沙箱镜像存在，如不存在则构建"""
        try:
            self.docker_client.images.get(self.sandbox_image)
        except docker.errors.NotFound:
            print(f"Image {self.sandbox_image} not found, building...")
            self._build_image()

    def _build_image(self):
        """构建沙箱镜像"""
        import subprocess
        dockerfile_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "sandbox", "docker")
        result = subprocess.run(
            ["docker", "build", "-t", self.sandbox_image, dockerfile_dir],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise RuntimeError(f"Failed to build image: {result.stderr}")
        print(f"Built image: {self.sandbox_image}")

    async def execute_test(
        self,
        run_id: str,
        code_content: str,
        test_type: str = "api",
        framework: str = "pytest"
    ) -> dict:
        """
        执行测试

        Args:
            run_id: 测试运行ID
            code_content: 测试代码内容
            test_type: 测试类型 (api/web)
            framework: 测试框架 (pytest)

        Returns:
            执行结果字典
        """
        container = None
        try:
            # 确保镜像存在
            self._ensure_image()

            # 1. 创建测试目录和文件
            test_dir = f"/tmp/test-run-{run_id}"
            os.makedirs(test_dir, exist_ok=True)

            if test_type == "api":
                # API 测试：写入 JSON 测试套件
                test_input = {
                    "name": f"API Test Run {run_id}",
                    "base_url": "",
                    "test_cases": json.loads(code_content) if code_content.startswith("[") else [{"name": "API Test", "request": json.loads(code_content)}]
                }
                test_file = f"{test_dir}/test_suite.json"
                with open(test_file, "w", encoding="utf-8") as f:
                    json.dump(test_input, f, ensure_ascii=False, indent=2)
                executor_script = "/app/executor/api_executor.py"
                output_file = "/app/report.json"
            else:
                # Web 测试：写入 JSON 测试套件
                test_input = {
                    "name": f"Web Test Run {run_id}",
                    "test_cases": json.loads(code_content) if code_content.startswith("[") else [{"name": "Web Test", "steps": json.loads(code_content)}]
                }
                test_file = f"{test_dir}/test_suite.json"
                with open(test_file, "w", encoding="utf-8") as f:
                    json.dump(test_input, f, ensure_ascii=False, indent=2)
                executor_script = "/app/executor/web_executor.py"
                output_file = "/app/report.json"

            # 2. 创建沙箱容器
            container = await self._create_sandbox(run_id)

            # 3. 复制测试文件到容器
            await self._copy_to_container(container, test_dir)

            # 4. 执行测试
            result = await self._run_executor(container, executor_script, test_file, output_file, framework)

            # 5. 获取报告
            report = await self._get_report(container, output_file)

            # 6. 获取日志
            logs = await self._get_logs(container)

            return {
                "status": "success" if result["exit_code"] == 0 else "failed",
                "exit_code": result["exit_code"],
                "logs": logs,
                "report": report,
                "duration_ms": result.get("duration_ms", 0),
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "logs": "",
                "report": None,
            }
        finally:
            if container:
                await self._destroy_sandbox(container)

    async def execute_pytest(
        self,
        run_id: str,
        code_content: str,
        requirements: Optional[str] = None
    ) -> dict:
        """
        执行 pytest 测试

        Args:
            run_id: 测试运行ID
            code_content: pytest 测试代码
            requirements: 可选的依赖 requirements.txt

        Returns:
            执行结果字典
        """
        container = None
        try:
            self._ensure_image()

            # 1. 创建测试目录
            test_dir = f"/tmp/test-run-{run_id}"
            os.makedirs(test_dir, exist_ok=True)

            # 2. 写入测试文件
            test_file = f"{test_dir}/test_sample.py"
            with open(test_file, "w", encoding="utf-8") as f:
                f.write(code_content)

            # 3. 写入 requirements.txt（如果提供）
            if requirements:
                req_file = f"{test_dir}/requirements.txt"
                with open(req_file, "w", encoding="utf-8") as f:
                    f.write(requirements)

            # 4. 创建沙箱容器
            container = await self._create_sandbox(run_id)

            # 5. 复制测试文件到容器
            await self._copy_to_container(container, test_dir)

            # 6. 安装依赖（如有）
            if requirements:
                await self._install_requirements(container, "/app/requirements.txt")

            # 7. 执行 pytest
            result = await self._run_pytest(container, "/app/test_sample.py")

            # 8. 获取日志
            logs = await self._get_logs(container)

            return {
                "status": "success" if result["exit_code"] == 0 else "failed",
                "exit_code": result["exit_code"],
                "logs": logs,
                "duration_ms": result.get("duration_ms", 0),
            }
        except Exception as e:
            return {
                "status": "failed",
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
            mem_limit="2g",
            cpu_period=100000,
            cpu_quota=200000,
            hostname=f"test-run-{run_id}",
            network=self.network_name,
            remove=False,
            command="sleep infinity"
        )
        # 等待容器启动
        await asyncio.sleep(2)
        return container

    async def _copy_to_container(self, container, src_dir: str):
        """复制文件到容器"""
        # 创建 tar 包
        tar_stream = await asyncio.to_thread(self._create_tar, src_dir)
        tar_stream.seek(0)

        # 复制到容器
        try:
            container.put_archive("/app", tar_stream)
        except Exception as e:
            print(f"put_archive error: {e}")
            # Fallback: 直接写入文件内容
            await self._copy_files_via_exec(container, src_dir)

    def _create_tar(self, src_dir: str):
        """创建 tar 包"""
        import io
        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode='w') as tar:
            for filename in os.listdir(src_dir):
                filepath = os.path.join(src_dir, filename)
                if os.path.isfile(filepath):
                    tar.add(filepath, arcname=filename)
        tar_stream.seek(0)
        return tar_stream

    async def _copy_files_via_exec(self, container, src_dir: str):
        """通过 exec 复制文件到容器"""
        for filename in os.listdir(src_dir):
            filepath = os.path.join(src_dir, filename)
            if os.path.isfile(filepath):
                with open(filepath, "rb") as f:
                    content = f.read()
                # 写入文件到容器
                import base64
                encoded = base64.b64encode(content).decode()
                exec_cmd = f"echo '{encoded}' | base64 -d > /app/{filename}"
                container.exec_run(["sh", "-c", exec_cmd])

    async def _run_executor(self, container, executor_script: str, input_file: str, output_file: str, framework: str) -> dict:
        """执行测试执行器"""
        start_time = datetime.now()

        # 选择执行器命令
        if "api_executor" in executor_script:
            cmd = f"python {executor_script} -i {input_file} -o {output_file}"
        elif "web_executor" in executor_script:
            cmd = f"python {executor_script} -i {input_file} -o {output_file}"
        else:
            cmd = f"python -m pytest {input_file} -v --tb=short"

        # 执行命令
        exec_result = container.exec_run(
            ["sh", "-c", cmd],
            socket=True,
            stream=True
        )

        logs = []
        exit_code = 0

        # 读取输出
        output = exec_result.output
        if hasattr(output, 'recv'):
            while True:
                try:
                    chunk = output.recv(4096)
                    if not chunk:
                        break
                    logs.append(chunk.decode('utf-8', errors='ignore'))
                except socket.timeout:
                    break
        else:
            for chunk in output:
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

    async def _run_pytest(self, container, test_file: str) -> dict:
        """执行 pytest"""
        start_time = datetime.now()

        exec_result = container.exec_run(
            ["python", "-m", "pytest", test_file, "-v", "--tb=short", "--json-report", "--json-report-file=/app/report.json"],
            socket=True,
            stream=True
        )

        logs = []
        exit_code = exec_result.exit_code

        output = exec_result.output
        if hasattr(output, 'recv'):
            while True:
                try:
                    chunk = output.recv(4096)
                    if not chunk:
                        break
                    logs.append(chunk.decode('utf-8', errors='ignore'))
                except socket.timeout:
                    break
        else:
            for chunk in output:
                if isinstance(chunk, bytes):
                    logs.append(chunk.decode('utf-8', errors='ignore'))
                else:
                    logs.append(str(chunk))

        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        return {
            "exit_code": exit_code,
            "logs": "".join(logs),
            "duration_ms": duration_ms
        }

    async def _install_requirements(self, container, requirements_file: str):
        """安装 Python 依赖"""
        container.exec_run(["pip", "install", "-r", requirements_file])

    async def _get_report(self, container, report_path: str) -> Optional[dict]:
        """获取测试报告"""
        try:
            import io
            bits, stat = container.get_archive(report_path)
            tar_stream = io.BytesIO()
            for chunk in bits:
                tar_stream.write(chunk)
            tar_stream.seek(0)

            with tarfile.open(fileobj=tar_stream) as tar:
                member = tar.getmember(os.path.basename(report_path))
                f = tar.extractfile(member)
                if f:
                    return json.loads(f.read().decode('utf-8'))
        except Exception:
            pass
        return None

    async def _get_logs(self, container, tail: int = 1000) -> str:
        """获取容器日志"""
        try:
            logs = container.logs(stdout=True, stderr=True, tail=tail).decode('utf-8', errors='ignore')
            return logs
        except Exception:
            return ""

    async def _destroy_sandbox(self, container):
        """销毁沙箱容器"""
        try:
            container.stop(timeout=5)
        except Exception:
            pass
        try:
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
