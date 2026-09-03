import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Text, Boolean, Integer, Float, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class QARun(Base):
    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    environment_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("environments.id", ondelete="SET NULL"), nullable=True, index=True)
    scan_type: Mapped[str] = mapped_column(String(50), default="QUICK_SCAN") # QUICK_SCAN, FULL_SCAN, REGRESSION_RUN, SCENARIO_RUN
    status: Mapped[str] = mapped_column(String(50), default="PENDING", index=True) # PENDING, RUNNING, COMPLETED, FAILED, CANCELLED
    trigger: Mapped[str] = mapped_column(String(50), default="MANUAL") # MANUAL, CLI, SCHEDULED
    browser: Mapped[str] = mapped_column(String(50), default="chromium")
    viewport_width: Mapped[int] = mapped_column(Integer, default=1920)
    viewport_height: Mapped[int] = mapped_column(Integer, default=1080)
    
    # Progress and counters
    pages_discovered: Mapped[int] = mapped_column(Integer, default=0)
    pages_tested: Mapped[int] = mapped_column(Integer, default=0)
    total_issues: Mapped[int] = mapped_column(Integer, default=0)
    critical_issues: Mapped[int] = mapped_column(Integer, default=0)
    high_issues: Mapped[int] = mapped_column(Integer, default=0)
    medium_issues: Mapped[int] = mapped_column(Integer, default=0)
    low_issues: Mapped[int] = mapped_column(Integer, default=0)
    info_issues: Mapped[int] = mapped_column(Integer, default=0)
    
    # QA score (0-100)
    qa_score: Mapped[float] = mapped_column(Float, default=100.0)
    
    # Regression stats
    new_issues_count: Mapped[int] = mapped_column(Integer, default=0)
    existing_issues_count: Mapped[int] = mapped_column(Integer, default=0)
    resolved_issues_count: Mapped[int] = mapped_column(Integer, default=0)
    regression_issues_count: Mapped[int] = mapped_column(Integer, default=0)
    
    current_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    current_action: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="runs")
    environment: Mapped[Optional["Environment"]] = relationship("Environment", back_populates="runs")
    page_visits: Mapped[List["PageVisit"]] = relationship("PageVisit", back_populates="run", cascade="all, delete-orphan")
    issue_occurrences: Mapped[List["IssueOccurrence"]] = relationship("IssueOccurrence", back_populates="run", cascade="all, delete-orphan")
    events: Mapped[List["RunEvent"]] = relationship("RunEvent", back_populates="run", cascade="all, delete-orphan")
    browser_sessions: Mapped[List["BrowserSession"]] = relationship("BrowserSession", back_populates="run", cascade="all, delete-orphan")

class RunEvent(Base):
    __tablename__ = "run_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("runs.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    level: Mapped[str] = mapped_column(String(20), default="INFO") # INFO, WARNING, ERROR, SUCCESS
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    data: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    # Relationships
    run: Mapped["QARun"] = relationship("QARun", back_populates="events")

class BrowserSession(Base):
    __tablename__ = "browser_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("runs.id", ondelete="CASCADE"), nullable=False, index=True)
    browser_name: Mapped[str] = mapped_column(String(50), default="chromium")
    viewport: Mapped[str] = mapped_column(String(50), default="1920x1080")
    is_headless: Mapped[bool] = mapped_column(Boolean, default=True)
    trace_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    video_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    run: Mapped["QARun"] = relationship("QARun", back_populates="browser_sessions")
