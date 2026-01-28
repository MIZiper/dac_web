from pydantic import BaseModel, Field, ConfigDict

from enum import Enum

class StatusType(Enum):
    Created = 0
    Configured = 1
    Completed = 2
    Failed = -1
    Unknown = -2

class Response(BaseModel):
    message: str

class DACConfig(BaseModel):
    model_config = ConfigDict(extra='allow')
    contexts: list[dict]
    actions: list[dict]

class ManProjectResp(Response):
    session_id: str | None = Field(..., alias="dac-sess_id")
    project_id: str | None = Field(...)

class DACConfigResp(Response):
    config: DACConfig

class ScenariosResp(Response):
    scenarios: list[str] | None
    current_scenario: str

class ActionsOfContextResp(BaseModel):
    name: str
    uuid: str
    status: int
    type: str
