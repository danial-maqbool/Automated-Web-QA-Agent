import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Boolean, Integer, Float, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class AccessibilityFinding(Base):
    __tablename__ = "accessibility_findings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    page_visit_id: Mapped[str] = mapped_column(String(36), ForeignKey("page_visits.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    impact: Mapped[str] = mapped_column(String(20), default="moderate", index=True) # critical, serious, moderate, minor
    description: Mapped[str] = mapped_column(Text, nullable=False)
    help_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    selector: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    html_snippet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    failure_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    page_visit: Mapped["PageVisit"] = relationship("PageVisit", back_populates="accessibility_findings")

class PerformanceMetric(Base):
    __tablename__ = "performance_metrics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    page_visit_id: Mapped[str] = mapped_column(String(36), ForeignKey("page_visits.id", ondelete="CASCADE"), nullable=False, index=True)
    ttfb_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    dom_content_loaded_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    load_time_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fcp_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True) # First Contentful Paint
    lcp_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True) # Largest Contentful Paint
    cls: Mapped[Optional[float]] = mapped_column(Float, nullable=True)    # Cumulative Layout Shift
    request_count: Mapped[int] = mapped_column(Integer, default=0)
    transfer_size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    budget_exceeded: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    page_visit: Mapped["PageVisit"] = relationship("PageVisit", back_populates="performance_metrics")
