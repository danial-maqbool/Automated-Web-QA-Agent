from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class TestStepSchema(BaseModel):
    order_index: int = 0
    action_type: str # navigate, click, fill, select, check, uncheck, wait, press_key, take_screenshot, assert_text, assert_element, assert_url, assert_visibility, assert_http_status, assert_no_console_errors
    target: Optional[str] = None
    value: Optional[str] = None
    expected_value: Optional[str] = None
    is_optional: bool = False

class TestScenarioCreate(BaseModel):
    name: str
    description: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list)
    steps: List[TestStepSchema] = Field(default_factory=list)

class TestStepResponse(TestStepSchema):
    id: str
    scenario_id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class TestScenarioResponse(BaseModel):
    id: str
    project_id: str
    name: str
    description: Optional[str] = None
    is_active: bool
    tags: Optional[List[str]] = Field(default_factory=list)
    steps: List[TestStepResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class TestSuiteCreate(BaseModel):
    name: str
    description: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list)
    scenario_ids: List[str] = Field(default_factory=list)

class TestSuiteResponse(BaseModel):
    id: str
    project_id: str
    name: str
    description: Optional[str] = None
    tags: Optional[List[str]] = Field(default_factory=list)
    scenario_ids: List[str] = Field(default_factory=list)
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
