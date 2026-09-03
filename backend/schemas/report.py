from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ReportSummary(BaseModel):
    project_id: str
    project_name: str
    run_id: str
    scan_type: str
    status: str
    qa_score: float
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: float
    
    total_pages_tested: int
    total_issues_found: int
    severity_breakdown: Dict[str, int]
    category_breakdown: Dict[str, int]
    
    critical_issues: List[Dict[str, Any]]
    high_issues: List[Dict[str, Any]]
    accessibility_summary: Dict[str, Any]
    performance_summary: Dict[str, Any]
    regression_summary: Dict[str, int]
    recommendations: List[str]
