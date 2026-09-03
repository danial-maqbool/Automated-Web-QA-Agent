import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Text, Boolean, Integer, Float, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Issue(Base):
    __tablename__ = "issues"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True) # Functional, Navigation, Form, Network, Console, Visual, Responsive, Accessibility, Performance, SEO, Content, Browser Compatibility, Regression, Configuration
    severity: Mapped[str] = mapped_column(String(20), nullable=False, index=True) # CRITICAL, HIGH, MEDIUM, LOW, INFO
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    status: Mapped[str] = mapped_column(String(20), default="OPEN", index=True) # OPEN, ACKNOWLEDGED, FIXED, IGNORED, REGRESSION
    
    description: Mapped[str] = mapped_column(Text, nullable=False)
    page_url: Mapped[str] = mapped_column(String(500), nullable=False)
    selector: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    expected_behavior: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    observed_behavior: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reproduction_steps: Mapped[Optional[List[dict]]] = mapped_column(JSON, default=list)
    
    # Evidence references
    screenshot_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    trace_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    network_evidence: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    console_evidence: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    
    # Context
    environment_name: Mapped[Optional[str]] = mapped_column(String(100), default="Production")
    browser: Mapped[str] = mapped_column(String(50), default="chromium")
    viewport: Mapped[str] = mapped_column(String(50), default="1920x1080")
    
    # Tracking
    occurrence_count: Mapped[int] = mapped_column(Integer, default=1)
    affected_pages_count: Mapped[int] = mapped_column(Integer, default=1)
    affected_pages: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    first_detected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_detected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="issues")
    occurrences: Mapped[List["IssueOccurrence"]] = relationship("IssueOccurrence", back_populates="issue", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_issue_proj_fingerprint", "project_id", "fingerprint", unique=True),
    )

class IssueOccurrence(Base):
    __tablename__ = "issue_occurrences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    issue_id: Mapped[str] = mapped_column(String(36), ForeignKey("issues.id", ondelete="CASCADE"), nullable=False, index=True)
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("runs.id", ondelete="CASCADE"), nullable=False, index=True)
    page_url: Mapped[str] = mapped_column(String(500), nullable=False)
    screenshot_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    issue: Mapped["Issue"] = relationship("Issue", back_populates="occurrences")
    run: Mapped["QARun"] = relationship("QARun", back_populates="issue_occurrences")
