import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Text, Boolean, Integer, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class TestScenario(Base):
    __test__ = False
    __tablename__ = "test_scenarios"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="test_scenarios")
    steps: Mapped[List["TestStep"]] = relationship("TestStep", back_populates="scenario", order_by="TestStep.order_index", cascade="all, delete-orphan")
    suite_members: Mapped[List["SuiteMember"]] = relationship("SuiteMember", back_populates="scenario", cascade="all, delete-orphan")

class TestStep(Base):
    __test__ = False
    __tablename__ = "test_steps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    scenario_id: Mapped[str] = mapped_column(String(36), ForeignKey("test_scenarios.id", ondelete="CASCADE"), nullable=False, index=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False) 
    # navigate, click, fill, select, check, uncheck, wait, press_key, take_screenshot,
    # assert_text, assert_element, assert_url, assert_visibility, assert_http_status, assert_no_console_errors
    target: Mapped[Optional[str]] = mapped_column(String(500), nullable=True) # selector or url
    value: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    expected_value: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_optional: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    scenario: Mapped["TestScenario"] = relationship("TestScenario", back_populates="steps")

class TestSuite(Base):
    __test__ = False
    __tablename__ = "test_suites"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="test_suites")
    members: Mapped[List["SuiteMember"]] = relationship("SuiteMember", back_populates="suite", order_by="SuiteMember.order_index", cascade="all, delete-orphan")

class SuiteMember(Base):
    __tablename__ = "suite_members"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    suite_id: Mapped[str] = mapped_column(String(36), ForeignKey("test_suites.id", ondelete="CASCADE"), nullable=False, index=True)
    scenario_id: Mapped[str] = mapped_column(String(36), ForeignKey("test_scenarios.id", ondelete="CASCADE"), nullable=False, index=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    suite: Mapped["TestSuite"] = relationship("TestSuite", back_populates="members")
    scenario: Mapped["TestScenario"] = relationship("TestScenario", back_populates="suite_members")
