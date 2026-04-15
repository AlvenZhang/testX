"""依赖注入 - 获取当前用户、校验权限"""
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.security import SECRET_KEY, ALGORITHM
from ..models.user import User
from ..models.project_member import ProjectMember

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    获取当前认证用户

    Returns:
        User: 当前登录用户

    Raises:
        HTTPException: 认证失败时抛出401
    """
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    # 从数据库获取用户
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    获取当前用户ID（不查询数据库）

    Returns:
        str: 当前用户ID
    """
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        return user_id
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    获取当前用户（可选，未认证返回None）

    Returns:
        Optional[User]: 当前登录用户或None
    """
    if credentials is None:
        return None

    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None

        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    except JWTError:
        return None


class RoleChecker:
    """角色检查器"""

    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    async def __call__(self, user: User = Depends(get_current_user)) -> User:
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user


# 预定义的角色检查器
require_admin = RoleChecker(["admin"])
require_user = RoleChecker(["admin", "user"])


async def check_project_permission(
    project_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    required_roles: Optional[list[str]] = None,
) -> User:
    """
    检查用户在项目中的权限

    Args:
        project_id: 项目ID
        user: 当前用户
        db: 数据库会话
        required_roles: 需要的角色列表，如 ["editor", "admin"]

    Returns:
        User: 当前用户

    Raises:
        HTTPException: 权限不足或项目不存在时抛出
    """
    # 管理员拥有所有项目权限
    if user.role == "admin":
        return user

    # 检查用户是否为项目成员
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user.id,
        )
    )
    member = result.scalar_one_or_none()

    if member is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this project",
        )

    # 如果没有指定需要的角色，只要项目成员即可
    if required_roles is None:
        return user

    # 检查用户角色是否在允许列表中
    if member.role not in required_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Required role: {required_roles}, your role: {member.role}",
        )

    return user


def require_project_role(*roles: str):
    """
    依赖工厂函数 - 生成检查项目角色的依赖

    Usage:
        @router.post("/{project_id}/...")
        async def update_project(
            project_id: str,
            db: AsyncSession = Depends(get_db),
            user: User = Depends(require_project_role("editor", "admin")),
        ):
            ...
    """
    async def dependency(
        project_id: str,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        return await check_project_permission(project_id, user, db, list(roles))

    return dependency
