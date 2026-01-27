from pydantic import BaseModel

class ActionsOfContextResp(BaseModel):
    name: str
    uuid: str
    status: int
    type: str