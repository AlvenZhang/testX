from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import uuid
import os
from datetime import datetime

from ...core.database import get_db
from ...core.config import get_settings
from ...models.requirement import Requirement, RequirementVersion
from ...schemas.requirement import (
    RequirementCreate, RequirementUpdate, RequirementResponse,
    RequirementVersionResponse, AttachmentInfo
)

router = APIRouter(prefix="/requirements", tags=["requirements"])


def compute_diff(old: dict, new: dict) -> dict:
    """计算两个版本之间的差异"""
    diff = {}
    if old.get("title") != new.get("title"):
        diff["title_changed"] = True
    if old.get("description") != new.get("description"):
        diff["description_changed"] = True
    return diff


@router.post("/", response_model=RequirementResponse, status_code=status.HTTP_201_CREATED)
async def create_requirement(
    requirement: RequirementCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建需求"""
    db_req = Requirement(
        id=str(uuid.uuid4()),
        project_id=requirement.project_id,
        title=requirement.title,
        description=requirement.description,
        priority=requirement.priority or "medium",
        extra=requirement.extra,
    )
    db.add(db_req)
    await db.commit()
    await db.refresh(db_req)
    return db_req


@router.get("/", response_model=List[RequirementResponse])
async def list_requirements(
    project_id: str,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """获取项目下的需求列表"""
    result = await db.execute(
        select(Requirement)
        .where(Requirement.project_id == project_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/{requirement_id}", response_model=RequirementResponse)
async def get_requirement(requirement_id: str, db: AsyncSession = Depends(get_db)):
    """获取需求详情"""
    result = await db.execute(select(Requirement).where(Requirement.id == requirement_id))
    requirement = result.scalar_one_or_none()
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return requirement


@router.put("/{requirement_id}", response_model=RequirementResponse)
async def update_requirement(
    requirement_id: str,
    requirement: RequirementUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新需求（自动创建版本历史）"""
    result = await db.execute(select(Requirement).where(Requirement.id == requirement_id))
    db_req = result.scalar_one_or_none()
    if not db_req:
        raise HTTPException(status_code=404, detail="Requirement not found")

    # 保存旧版本
    old_data = {"title": db_req.title, "description": db_req.description}
    new_version = db_req.version + 1

    # 创建版本记录
    version_entry = RequirementVersion(
        id=str(uuid.uuid4()),
        requirement_id=requirement_id,
        version=db_req.version,
        title=db_req.title,
        description=db_req.description,
        diff={},
    )
    db.add(version_entry)

    # 更新需求
    update_data = requirement.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_req, key, value)
    db_req.version = new_version

    # 创建新版本（diff）
    new_data = {"title": db_req.title, "description": db_req.description}
    version_entry.diff = compute_diff(old_data, new_data)

    await db.commit()
    await db.refresh(db_req)
    return db_req


@router.delete("/{requirement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_requirement(requirement_id: str, db: AsyncSession = Depends(get_db)):
    """删除需求"""
    result = await db.execute(select(Requirement).where(Requirement.id == requirement_id))
    requirement = result.scalar_one_or_none()
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    await db.delete(requirement)
    await db.commit()


@router.get("/{requirement_id}/versions", response_model=List[RequirementVersionResponse])
async def get_requirement_versions(requirement_id: str, db: AsyncSession = Depends(get_db)):
    """获取需求版本历史"""
    result = await db.execute(
        select(RequirementVersion)
        .where(RequirementVersion.requirement_id == requirement_id)
        .order_by(RequirementVersion.version.desc())
    )
    return result.scalars().all()


@router.post("/{requirement_id}/attachments")
async def upload_attachment(
    requirement_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """上传需求附件"""
    result = await db.execute(select(Requirement).where(Requirement.id == requirement_id))
    requirement = result.scalar_one_or_none()
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    # 创建上传目录
    settings = get_settings()
    upload_dir = os.path.join(settings.uploads_dir or "/tmp/uploads", requirement_id)
    os.makedirs(upload_dir, exist_ok=True)

    # 保存文件
    file_path = os.path.join(upload_dir, file.filename)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # 更新附件列表
    attachment = AttachmentInfo(
        name=file.filename,
        url=f"/uploads/{requirement_id}/{file.filename}",
        size=len(content),
        type=file.content_type or "application/octet-stream",
    )

    attachments = requirement.attachments or []
    attachments.append(attachment.model_dump())
    requirement.attachments = attachments

    await db.commit()
    await db.refresh(requirement)

    return {"attachment": attachment, "total_attachments": len(attachments)}


@router.delete("/{requirement_id}/attachments/{filename}")
async def delete_attachment(
    requirement_id: str,
    filename: str,
    db: AsyncSession = Depends(get_db),
):
    """删除需求附件"""
    result = await db.execute(select(Requirement).where(Requirement.id == requirement_id))
    requirement = result.scalar_one_or_none()
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    attachments = requirement.attachments or []
    attachment_to_delete = next((a for a in attachments if a.get("name") == filename), None)

    if not attachment_to_delete:
        raise HTTPException(status_code=404, detail="Attachment not found")

    # 删除文件
    file_path = attachment_to_delete.get("url", "").lstrip("/")
    if os.path.exists(file_path):
        os.remove(file_path)

    # 更新附件列表
    attachments = [a for a in attachments if a.get("name") != filename]
    requirement.attachments = attachments

    await db.commit()
    await db.refresh(requirement)

    return {"deleted": True, "remaining_attachments": len(attachments)}


@router.post("/{requirement_id}/git-link")
async def link_git_info(
    requirement_id: str,
    git_info: dict,
    db: AsyncSession = Depends(get_db),
):
    """关联Git信息到需求"""
    result = await db.execute(select(Requirement).where(Requirement.id == requirement_id))
    requirement = result.scalar_one_or_none()
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    if commit_sha := git_info.get("commit_sha"):
        requirement.git_commit_sha = commit_sha
    if pr_number := git_info.get("pr_number"):
        requirement.git_pr_number = pr_number
    if diff_url := git_info.get("diff_url"):
        requirement.git_diff_url = diff_url

    await db.commit()
    await db.refresh(requirement)

    return {
        "git_commit_sha": requirement.git_commit_sha,
        "git_pr_number": requirement.git_pr_number,
        "git_diff_url": requirement.git_diff_url,
    }


@router.get("/{requirement_id}/code-changes")
async def get_linked_code_changes(requirement_id: str, db: AsyncSession = Depends(get_db)):
    """获取关联的代码变更"""
    result = await db.execute(select(Requirement).where(Requirement.id == requirement_id))
    requirement = result.scalar_one_or_none()
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    from ...models.code_change import CodeChange
    result = await db.execute(
        select(CodeChange)
        .where(CodeChange.requirement_id == requirement_id)
        .order_by(CodeChange.created_at.desc())
    )
    code_changes = result.scalars().all()

    return [
        {
            "id": cc.id,
            "commit_sha": cc.commit_sha,
            "pr_number": cc.pr_number,
            "diff_url": cc.diff_url,
            "status": cc.status,
            "created_at": cc.created_at,
        }
        for cc in code_changes
    ]


@router.get("/status-flow")
async def get_status_flow():
    """获取需求状态流转定义"""
    return {
        "statuses": [
            {"value": "pending", "label": "待分析", "color": "default"},
            {"value": "cases_generated", "label": "已生成用例", "color": "processing"},
            {"value": "code_generated", "label": "已生成代码", "color": "blue"},
            {"value": "tested", "label": "已测试", "color": "success"},
        ],
        "transitions": {
            "pending": ["cases_generated"],
            "cases_generated": ["code_generated", "pending"],
            "code_generated": ["tested", "cases_generated"],
            "tested": ["code_generated"],
        },
    }
