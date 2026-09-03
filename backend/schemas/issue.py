from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class IssueUpdate(BaseModel):
    status: Optional[str] = None # OPEN, ACKNOWLEDGED, FIXED, IGNORED, REGRESSION
    severity: Optional[str] = None # CRITICAL, HIGH, MEDIUM, LOW, INFO
    notes: Optional[str] = None

class IssueOccurrenceResponse(BaseModel):
    id: str
    issue_id: str
    run_id: str
    page_url: str
    screenshot_path: Optional[str] = None
    detected_at: datetime
    model_config = ConfigDict(from_attributes=True)

class IssueResponse(BaseModel):
    id: str
    project_id: str
    fingerprint: str
    title: str
    category: str
    severity: str
    confidence: float
    status: str
    description: str
    page_url: str
    selector: Optional[str] = None
    expected_behavior: Optional[str] = None
    observed_behavior: Optional[str] = None
    reproduction_steps: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    
    screenshot_path: Optional[str] = None
    trace_path: Optional[str] = None
    network_evidence: Optional[Dict[str, Any]] = Field(default_factory=dict)
    console_evidence: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    environment_name: Optional[str] = "Production"
    browser: str = "chromium"
    viewport: str = "1920x1080"
    
    occurrence_count: int
    affected_pages_count: int
    affected_pages: Optional[List[str]] = Field(default_factory=list)
    notes: Optional[str] = None
    
    first_detected_at: datetime
    last_detected_at: datetime
    model_config = ConfigDict(from_attributes=True)
