import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Text, Boolean, Integer, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    base_url: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    allowed_domains: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    settings: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    environments: Mapped[List["Environment"]] = relationship("Environment", back_populates="project", cascade="all, delete-orphan")
    runs: Mapped[List["QARun"]] = relationship("QARun", back_populates="project", cascade="all, delete-orphan")
    pages: Mapped[List["Page"]] = relationship("Page", back_populates="project", cascade="all, delete-orphan")
    issues: Mapped[List["Issue"]] = relationship("Issue", back_populates="project", cascade="all, delete-orphan")
    ignore_rules: Mapped[List["IgnoreRule"]] = relationship("IgnoreRule", back_populates="project", cascade="all, delete-orphan")
    test_scenarios: Mapped[List["TestScenario"]] = relationship("TestScenario", back_populates="project", cascade="all, delete-orphan")
    test_suites: Mapped[List["TestSuite"]] = relationship("TestSuite", back_populates="project", cascade="all, delete-orphan")
    baselines: Mapped[List["Baseline"]] = relationship("Baseline", back_populates="project", cascade="all, delete-orphan")

class Environment(Base):
    __tablename__ = "environments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False) # Development, Staging, Production
    base_url: Mapped[str] = mapped_column(String(500), nullable=False)
    headers: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    cookies: Mapped[Optional[List[dict]]] = mapped_column(JSON, default=list)
    auth_storage_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    crawl_depth: Mapped[int] = mapped_column(Integer, default=3)
    max_pages: Mapped[int] = mapped_column(Integer, default=50)
    timeout_ms: Mapped[int] = mapped_column(Integer, default=30000)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="environments")
    runs: Mapped[List["QARun"]] = relationship("QARun", back_populates="environment")

class IgnoreRule(Base):
    __tablename__ = "ignore_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False) # url_regex, selector, console_regex, rule_id, endpoint_regex
    pattern: Mapped[str] = mapped_column(String(500), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="ignore_rules")
