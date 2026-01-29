from pydantic import BaseModel, Field, ConfigDict

from enum import Enum


class StatusType(Enum):
    Created = 0
    Configured = 1
    Completed = 2
    Failed = -1
    Unknown = -2


class DACRequest(BaseModel):
    pass


class DACResponse(BaseModel):
    message: str


class DACConfig(BaseModel):
    model_config = ConfigDict(extra="allow")
    contexts: list[dict]
    actions: list[dict]


class DACNodeType(BaseModel):
    name: str
    type: str


class DACData(BaseModel):
    name: str
    uuid: str | None = None
    type: str


class DACAction(BaseModel):
    name: str
    uuid: str | None
    status: StatusType
    type: str


class DACContext(BaseModel):
    name: str
    uuid: str | None = None
    type: str


class ManProjectResp(DACResponse):
    dac_sess_id: str | None = Field(..., alias="session_id")
    project_id: str | None = Field(...)


class SaveProjectReq(DACRequest):
    project_id: str
    publish_name: str
    signature: str


class ProjectConfigResp(DACResponse):
    config: DACConfig


class ScenarioReq(DACRequest):
    scenario: str


class ScenariosResp(DACResponse):
    scenarios: list[str] | None
    current_scenario: str


class DataReq(DACRequest):
    data_config: DACData


class DataResp(DACResponse):
    data: list[DACData]


class ActionReq(DACRequest):
    action_config: DACAction


class ActionResp(DACResponse):
    action_uuid: str


class ActionsResp(DACResponse):
    actions: list[DACAction]


class ActionRunResp(DACResponse):
    data_updated: bool
    status: StatusType
    stats: object


class ContextReq(DACRequest):
    context_config: DACContext


class ContextResp(DACResponse):
    context_uuid: str


class ContextsResp(DACResponse):
    contexts: list[DACContext]
    current_context: str


class TypesResp(DACResponse):
    context_types: list[DACNodeType | str] | None = None
    action_types: list[DACNodeType | str] | None = None
