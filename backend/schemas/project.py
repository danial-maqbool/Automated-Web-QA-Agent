from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class EnvironmentBase(BaseModel):
    name: str
    base_url: str
    headers: Optional[Dict[str, str]] = Field(default_factory=dict)
    cookies: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    crawl_depth: int = 3
    max_pages: int = 50
    timeout_ms: int = 30000
    is_default: bool = False

class EnvironmentCreate(EnvironmentBase):
    pass

class EnvironmentResponse(EnvironmentBase):
    id: str
    project_id: str
    auth_storage_path: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class IgnoreRuleBase(BaseModel):
    rule_type: str # url_regex, selector, console_regex, rule_id, endpoint_regex
    pattern: str
    reason: Optional[str] = None
    is_active: bool = True

class IgnoreRuleCreate(IgnoreRuleBase):
    pass

class IgnoreRuleResponse(IgnoreRuleBase):
    id: str
    project_id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ProjectBase(BaseModel):
    name: str
    base_url: str
    description: Optional[str] = None
    allowed_domains: Optional[List[str]] = Field(default_factory=list)
    tags: Optional[List[str]] = Field(default_factory=list)
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ProjectCreate(ProjectBase):
    environments: Optional[List[EnvironmentCreate]] = None

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    base_url: Optional[str] = None
    description: Optional[str] = None
    allowed_domains: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    settings: Optional[Dict[str, Any]] = None

class ProjectResponse(ProjectBase):
    id: str
    created_at: datetime
    updated_at: datetime
    environments: List[EnvironmentResponse] = Field(default_factory=list)
    ignore_rules: List[IgnoreRuleResponse] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)
