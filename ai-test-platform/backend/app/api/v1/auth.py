"""用户认证 API"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import uuid

from ...core.database import get_db
from ...core.security import verify_password, get_password_hash, create_access_token, decode_token
from ...models.user import User
from ...services.ai_service import AIService

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str
    name: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """注册新用户"""
    # 检查邮箱是否已存在
    result = await db.execute(select(User).where(User.email == request.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # 创建用户
    user = User(
        id=str(uuid.uuid4()),
        email=request.email,
        name=request.name,
        password_hash=get_password_hash(request.password),
        role="user",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # 生成令牌
    access_token = create_access_token({"sub": user.id, "email": user.email})

    return LoginResponse(
        access_token=access_token,
        user={"id": user.id, "email": user.email, "name": user.name, "role": user.role}
    )


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """用户登录"""
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # 生成令牌
    access_token = create_access_token({"sub": user.id, "email": user.email})

    return LoginResponse(
        access_token=access_token,
        user={"id": user.id, "email": user.email, "name": user.name, "role": user.role}
    )
