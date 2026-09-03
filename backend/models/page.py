import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Text, Boolean, Integer, Float, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Page(Base):
    __tablename__ = "pages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    load_time_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    screenshot_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    last_tested_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="pages")
    page_visits: Mapped[List["PageVisit"]] = relationship("PageVisit", back_populates="page", cascade="all, delete-orphan")
    baselines: Mapped[List["Baseline"]] = relationship("Baseline", back_populates="page", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_page_project_url", "project_id", "url", unique=True),
    )

class PageVisit(Base):
    __tablename__ = "page_visits"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("runs.id", ondelete="CASCADE"), nullable=False, index=True)
    page_id: Mapped[str] = mapped_column(String(36), ForeignKey("pages.id", ondelete="CASCADE"), nullable=False, index=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    load_time_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    viewport: Mapped[str] = mapped_column(String(50), default="1920x1080")
    depth: Mapped[int] = mapped_column(Integer, default=0)
    discovered_via: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    meta_info: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    screenshot_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    visited_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    run: Mapped["QARun"] = relationship("QARun", back_populates="page_visits")
    page: Mapped["Page"] = relationship("Page", back_populates="page_visits")
    screenshots: Mapped[List["Screenshot"]] = relationship("Screenshot", back_populates="page_visit", cascade="all, delete-orphan")
    network_requests: Mapped[List["NetworkRequest"]] = relationship("NetworkRequest", back_populates="page_visit", cascade="all, delete-orphan")
    console_messages: Mapped[List["ConsoleMessage"]] = relationship("ConsoleMessage", back_populates="page_visit", cascade="all, delete-orphan")
    accessibility_findings: Mapped[List["AccessibilityFinding"]] = relationship("AccessibilityFinding", back_populates="page_visit", cascade="all, delete-orphan")
    performance_metrics: Mapped[List["PerformanceMetric"]] = relationship("PerformanceMetric", back_populates="page_visit", cascade="all, delete-orphan")
