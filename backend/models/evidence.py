import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Boolean, Integer, Float, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Screenshot(Base):
    __tablename__ = "screenshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    page_visit_id: Mapped[str] = mapped_column(String(36), ForeignKey("page_visits.id", ondelete="CASCADE"), nullable=False, index=True)
    screenshot_type: Mapped[str] = mapped_column(String(50), default="viewport") # full_page, viewport, element
    selector: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    width: Mapped[int] = mapped_column(Integer, default=1920)
    height: Mapped[int] = mapped_column(Integer, default=1080)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    page_visit: Mapped["PageVisit"] = relationship("PageVisit", back_populates="screenshots")

class NetworkRequest(Base):
    __tablename__ = "network_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    page_visit_id: Mapped[str] = mapped_column(String(36), ForeignKey("page_visits.id", ondelete="CASCADE"), nullable=False, index=True)
    method: Mapped[str] = mapped_column(String(10), default="GET")
    url: Mapped[str] = mapped_column(String(1000), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(50), default="document")
    status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    duration_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    failed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    failure_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    page_visit: Mapped["PageVisit"] = relationship("PageVisit", back_populates="network_requests")

class ConsoleMessage(Base):
    __tablename__ = "console_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    page_visit_id: Mapped[str] = mapped_column(String(36), ForeignKey("page_visits.id", ondelete="CASCADE"), nullable=False, index=True)
    message_type: Mapped[str] = mapped_column(String(20), default="error", index=True) # error, warning, info
    text: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    stack_trace: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    page_visit: Mapped["PageVisit"] = relationship("PageVisit", back_populates="console_messages")
