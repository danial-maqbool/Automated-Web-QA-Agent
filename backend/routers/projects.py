from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models import Project, Environment, IgnoreRule
from backend.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectResponse,
    EnvironmentCreate, EnvironmentResponse,
    IgnoreRuleCreate, IgnoreRuleResponse
)

router = APIRouter(prefix="/api/projects", tags=["Projects"])

@router.get("", response_model=List[ProjectResponse])
async def list_projects(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Project)
        .options(selectinload(Project.environments), selectinload(Project.ignore_rules))
        .order_by(Project.created_at.desc())
    )
    return result.scalars().all()

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(payload: ProjectCreate, db: AsyncSession = Depends(get_db)):
    project = Project(
        name=payload.name,
        base_url=payload.base_url,
        description=payload.description,
        allowed_domains=payload.allowed_domains or [],
        tags=payload.tags or [],
        settings=payload.settings or {}
    )
    db.add(project)
    await db.flush()

    # Create default environments if provided, or create Production by default
    if payload.environments:
        for env_in in payload.environments:
            env = Environment(
                project_id=project.id,
                name=env_in.name,
                base_url=env_in.base_url,
                headers=env_in.headers or {},
                cookies=env_in.cookies or [],
                crawl_depth=env_in.crawl_depth,
                max_pages=env_in.max_pages,
                timeout_ms=env_in.timeout_ms,
                is_default=env_in.is_default
            )
            db.add(env)
    else:
        default_env = Environment(
            project_id=project.id,
            name="Production",
            base_url=project.base_url,
            is_default=True
        )
        db.add(default_env)

    await db.commit()
    
    # Reload with relations
    result = await db.execute(
        select(Project)
        .options(selectinload(Project.environments), selectinload(Project.ignore_rules))
        .where(Project.id == project.id)
    )
    return result.scalar_one()

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Project)
        .options(selectinload(Project.environments), selectinload(Project.ignore_rules))
        .where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, payload: ProjectUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(project, k, v)
        
    await db.commit()
    return await get_project(project_id, db)

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await db.delete(project)
    await db.commit()
    return None
