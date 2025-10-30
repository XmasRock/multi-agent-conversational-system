# raspberry-pi/mcp-server/models.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class AgentRegistration(BaseModel):
    agent_id: str
    agent_type: str
    capabilities: List[str] = []
    metadata: Dict[str, Any] = {}

class ContextUpdate(BaseModel):
    agent_id: str
    context_type: str
    data: Dict[str, Any]
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    priority: int = Field(default=1, ge=1, le=5)

class AgentQuery(BaseModel):
    requesting_agent: str
    query_type: str
    parameters: Dict[str, Any] = {}

class ActionRequest(BaseModel):
    requesting_agent: str
    target_agent: str
    action: str
    parameters: Dict[str, Any] = {}
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

class ActionResponse(BaseModel):
    request_id: str
    status: str  # success, error, processing
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())