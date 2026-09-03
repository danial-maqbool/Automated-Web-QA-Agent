import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, Boolean, Integer, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Baseline(Base):
    __tablename__ = "baselines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    page_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("pages.id", ondelete="SET NULL"), nullable=True, index=True)
    page_url: Mapped[str] = mapped_column(String(500), nullable=False)
    viewport: Mapped[str] = mapped_column(String(50), default="1920x1080")
    browser: Mapped[str] = mapped_column(String(50), default="chromium")
    screenshot_path: Mapped[str] = mapped_column(String(500), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="baselines")
    page: Mapped[Optional["Page"]] = relationship("Page", back_populates="baselines")
    comparisons: Mapped[List["VisualComparison"]] = relationship("VisualComparison", back_populates="baseline", cascade="all, delete-orphan")

class VisualComparison(Base):
    __tablename__ = "visual_comparisons"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("runs.id", ondelete="CASCADE"), nullable=False, index=True)
    baseline_id: Mapped[str] = mapped_column(String(36), ForeignKey("baselines.id", ondelete="CASCADE"), nullable=False, index=True)
    page_url: Mapped[str] = mapped_column(String(500), nullable=False)
    current_screenshot_path: Mapped[str] = mapped_column(String(500), nullable=False)
    diff_screenshot_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    diff_pixel_count: Mapped[int] = mapped_column(Integer, default=0)
    diff_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    passed: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    baseline: Mapped["Baseline"] = relationship("Baseline", back_populates="comparisons")
