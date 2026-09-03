from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class BaselineResponse(BaseModel):
    id: str
    project_id: str
    page_id: Optional[str] = None
    page_url: str
    viewport: str
    browser: str
    screenshot_path: str
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class VisualComparisonResponse(BaseModel):
    id: str
    run_id: str
    baseline_id: str
    page_url: str
    current_screenshot_path: str
    diff_screenshot_path: Optional[str] = None
    diff_pixel_count: int
    diff_percentage: float
    passed: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
