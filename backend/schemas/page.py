from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class ScreenshotResponse(BaseModel):
    id: str
    screenshot_type: str
    selector: Optional[str] = None
    file_path: str
    width: int
    height: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class NetworkRequestResponse(BaseModel):
    id: str
    method: str
    url: str
    resource_type: str
    status_code: Optional[int] = None
    duration_ms: Optional[float] = None
    size_bytes: Optional[int] = None
    failed: bool
    failure_reason: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ConsoleMessageResponse(BaseModel):
    id: str
    message_type: str
    text: str
    location: Optional[str] = None
    stack_trace: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class AccessibilityFindingResponse(BaseModel):
    id: str
    rule_id: str
    impact: str
    description: str
    help_url: Optional[str] = None
    selector: Optional[str] = None
    html_snippet: Optional[str] = None
    failure_summary: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class PerformanceMetricResponse(BaseModel):
    id: str
    ttfb_ms: Optional[float] = None
    dom_content_loaded_ms: Optional[float] = None
    load_time_ms: Optional[float] = None
    fcp_ms: Optional[float] = None
    lcp_ms: Optional[float] = None
    cls: Optional[float] = None
    request_count: int
    transfer_size_bytes: int
    budget_exceeded: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class PageResponse(BaseModel):
    id: str
    project_id: str
    url: str
    path: str
    title: Optional[str] = None
    status_code: Optional[int] = None
    load_time_ms: Optional[float] = None
    screenshot_path: Optional[str] = None
    last_tested_at: Optional[datetime] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class PageVisitResponse(BaseModel):
    id: str
    run_id: str
    page_id: str
    url: str
    status_code: Optional[int] = None
    title: Optional[str] = None
    load_time_ms: Optional[float] = None
    viewport: str
    depth: int
    discovered_via: Optional[str] = None
    meta_info: Optional[Dict[str, Any]] = Field(default_factory=dict)
    screenshot_path: Optional[str] = None
    visited_at: datetime
    
    screenshots: List[ScreenshotResponse] = Field(default_factory=list)
    network_requests: List[NetworkRequestResponse] = Field(default_factory=list)
    console_messages: List[ConsoleMessageResponse] = Field(default_factory=list)
    accessibility_findings: List[AccessibilityFindingResponse] = Field(default_factory=list)
    performance_metrics: List[PerformanceMetricResponse] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)
