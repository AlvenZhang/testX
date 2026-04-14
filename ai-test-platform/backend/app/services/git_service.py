"""Git 服务 - 用于获取代码变更"""
import subprocess
from typing import Optional
import re


class GitService:
    """Git 操作服务"""

    @staticmethod
    def clone_repo(git_url: str, dest_path: str) -> bool:
        """克隆 Git 仓库"""
        try:
            result = subprocess.run(
                ["git", "clone", git_url, dest_path],
                capture_output=True,
                text=True,
                timeout=300
            )
            return result.returncode == 0
        except Exception:
            return False

    @staticmethod
    def get_commit_diff(repo_path: str, commit_hash: str) -> Optional[str]:
        """获取某个提交的 diff"""
        try:
            result = subprocess.run(
                ["git", "-C", repo_path, "show", "--format=", commit_hash],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                return result.stdout
            return None
        except Exception:
            return None

    @staticmethod
    def get_commit_info(repo_path: str, commit_hash: str) -> Optional[dict]:
        """获取提交信息"""
        try:
            result = subprocess.run(
                ["git", "-C", repo_path, "show", "--format=%H|%an|%ae|%at|%s", "-s", commit_hash],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                parts = result.stdout.strip().split("|")
                if len(parts) >= 5:
                    return {
                        "hash": parts[0],
                        "author_name": parts[1],
                        "author_email": parts[2],
                        "timestamp": int(parts[3]),
                        "subject": parts[4]
                    }
            return None
        except Exception:
            return None

    @staticmethod
    def get_file_diff(repo_path: str, commit_hash: str, file_path: str) -> Optional[str]:
        """获取某个文件在某个提交中的 diff"""
        try:
            result = subprocess.run(
                ["git", "-C", repo_path, "show", "--format=", "-p", f"{commit_hash}", "--", file_path],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                return result.stdout
            return None
        except Exception:
            return None

    @staticmethod
    def extract_repo_info(git_url: str) -> dict:
        """从 Git URL 提取仓库信息"""
        # 支持多种 Git URL 格式
        patterns = [
            r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$",
            r"gitlab\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$",
            r"gitee\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$",
        ]
        for pattern in patterns:
            match = re.search(pattern, git_url)
            if match:
                return {
                    "host": match.group(1),
                    "repo": match.group(2).replace(".git", ""),
                    "type": "github" if "github" in pattern else "gitlab" if "gitlab" in pattern else "gitee"
                }
        return {"host": None, "repo": None, "type": "unknown"}
