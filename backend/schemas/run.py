from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class RunCreate(BaseModel):
    project_id: str
    environment_id: Optional[str] = None
    scan_type: str = "QUICK_SCAN" # QUICK_SCAN, FULL_SCAN, REGRESSION_RUN, SCENARIO_RUN
    browser: str = "chromium"
    viewport_width: int = 1920
    viewport_height: int = 1080
    trigger: str = "MANUAL"

class RunEventResponse(BaseModel):
    id: str
    run_id: str
    timestamp: datetime
    level: str
    message: str
    url: Optional[str] = None
    data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    model_config = ConfigDict(from_attributes=True)

class QARunResponse(BaseModel):
    id: str
    project_id: str
    environment_id: Optional[str] = None
    scan_type: str
    status: str
    trigger: str
    browser: str
    viewport_width: int
    viewport_height: int
    
    pages_discovered: int
    pages_tested: int
    total_issues: int
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    info_issues: int
    qa_score: float
    
    new_issues_count: int
    existing_issues_count: int
    resolved_issues_count: int
    regression_issues_count: int
    
    current_url: Optional[str] = None
    current_action: Optional[str] = None
    error_message: Optional[str] = None
    
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
