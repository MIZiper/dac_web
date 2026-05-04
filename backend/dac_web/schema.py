from pydantic import BaseModel, Field, ConfigDict
from dac.core import ActionNode

SESSID_KEY = "dac-sess_id"


class DACRequest(BaseModel):
    pass


class DACResponse(BaseModel):
    message: str


class DACConfig(BaseModel):
    model_config = ConfigDict(extra="allow")
    contexts: list[dict]
    actions: list[dict]


class DACFile(BaseModel):
    dac: DACConfig


class NodeType(BaseModel):
    name: str
    type: str

class NodeConfig(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: str


class DataMeta(BaseModel):
    name: str
    uuid: str | None = None
    type: str
    children: list["DataMeta"] | None = None


class ActionMeta(BaseModel):
    name: str
    uuid: str | None = None
    status: ActionNode.ActionStatus
    type: str

class QuickAction(BaseModel):
    data_path: str
    action_path: str
    action_name: str
    idx: int

class ContextMeta(BaseModel):
    name: str
    uuid: str | None = None
    type: str

class InitProjectReq(DACRequest):
    project_id: str

class ManProjectResp(DACResponse):
    session_id: str | None = Field(..., alias=SESSID_KEY)
    project_id: str | None = Field(...)


class SaveProjectReq(DACRequest):
    project_id: str
    publish_name: str
    signature: str = ""


class KeycloakStatus(BaseModel):
    keycloak_enabled: bool
    keycloak_url: str = ""
    keycloak_realm: str = ""
    keycloak_client_id: str = ""


class ProjectConfigResp(DACResponse):
    config: DACConfig


class ScenarioReq(DACRequest):
    scenario: str


class ScenariosResp(DACResponse):
    scenarios: list[str] | None
    current_scenario: str
    quick_actions: list[QuickAction] | None = None


class DatumCreate(DACRequest):
    data_config: DataMeta

class DatumExchange(BaseModel):
    data_config: NodeConfig


class DataResp(DACResponse):
    data: list[DataMeta]


# rebuild models to resolve forward references for recursive DataMeta
DataMeta.model_rebuild()


class ActionCreate(DACRequest):
    action_config: ActionMeta

class ActionCreateResp(DACResponse):
    action_uuid: str

class ActionExchange(BaseModel):
    action_config: NodeConfig
    

class ActionsResp(DACResponse):
    actions: list[ActionMeta]



class ContextCreate(DACRequest):
    context_config: ContextMeta

class ContextCreateResp(DACResponse):
    context_uuid: str

class ContextExchange(BaseModel):
    context_config: NodeConfig


class ContextsResp(DACResponse):
    contexts: list[ContextMeta]
    current_context: str


class TypesResp(DACResponse):
    context_types: list[NodeType | str] | None = None
    action_types: list[NodeType | str] | None = None


class ProjectItem(BaseModel):
    id: str
    created_at: str
    updated_at: str
    publish_title: str | None = None
    publish_status: str | None = None


class ProjectListResp(DACResponse):
    projects: list[ProjectItem]
    total: int
    page: int
    page_size: int
