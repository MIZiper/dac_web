from pydantic import BaseModel, Field, ConfigDict
from dac.core import ActionNode

SESSID_KEY = "dac-sess_id"


class DACRequest(BaseModel):
    pass


class DACResponse(BaseModel):
    message: str


class DACConfig(BaseModel):
    model_config = ConfigDict(extra="allow")
    contexts: list[dict] = Field(default_factory=list)
    actions: list[dict] = Field(default_factory=list)


class ProjectConfig(BaseModel):
    """Unified project config matching the storage format {"dac": ..., "dac_web": ...}."""
    model_config = ConfigDict(extra="allow")
    dac: DACConfig = Field(default_factory=lambda: DACConfig(contexts=[], actions=[]))
    dac_web: dict = Field(default_factory=dict)


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
    qualified_name: str | None = None
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
    mode: str | bool = False

class ContextMeta(BaseModel):
    name: str
    uuid: str | None = None
    type: str

class InitProjectReq(DACRequest):
    project_id: str

class ManProjectResp(DACResponse):
    session_id: str | None = Field(..., alias=SESSID_KEY)
    project_id: str | None = Field(...)
    title: str | None = Field(None)


class SaveProjectReq(DACRequest):
    project_id: str
    title: str = ""
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
    title: str | None = None
    creator_name: str | None = None


class ProjectListResp(DACResponse):
    projects: list[ProjectItem]
    total: int
    page: int
    page_size: int


class ProjectExportResp(DACResponse):
    project_id: str
    config: ProjectConfig


class ProjectImportReq(BaseModel):
    config: ProjectConfig
    project_id: str | None = None
    signature: str = ""


class ProjectImportResp(DACResponse):
    project_id: str
    title: str | None = None


# ── Import-Preview / Import-Apply (two-phase import with action replacement) ──


from enum import Enum as _Enum


class ReplacementStatus(str, _Enum):
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"
    UNCHANGED = "unchanged"


class ActionReplacementItem(BaseModel):
    """One action replacement proposed by a rule during import preview."""
    action_index: int
    action_uuid: str
    original: dict
    replacement: dict | None = None
    rule_name: str | None = None
    status: ReplacementStatus
    summary: str
    reason: str = ""


class ImportPreviewSummary(BaseModel):
    total_actions: int
    resolved: int
    unresolved: int
    unchanged: int


class ImportPreviewReq(BaseModel):
    config: ProjectConfig


class ImportPreviewResp(DACResponse):
    replacements: list[ActionReplacementItem]
    summary: ImportPreviewSummary


class ActionDecision(BaseModel):
    """User's decision on one replacement."""
    action_index: int
    action_uuid: str
    approved: bool
    override_replacement: dict | None = None


class ImportApplyReq(BaseModel):
    config: ProjectConfig
    decisions: list[ActionDecision]
    title: str = ""
    signature: str = ""


class ImportApplyResp(DACResponse):
    project_id: str
    title: str | None = None
