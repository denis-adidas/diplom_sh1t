import datetime
from pydantic import BaseModel
from  typing import Optional

# BASE MODELS
class StudentOrm(BaseModel):
    id: int
    name: str
    group_id: int
    created_at: str
    updated_at: str

class GroupOrm(BaseModel):
    id: int
    name: str

# REQUESTS
class PostStudentWithGroupsRequest(BaseModel):
    students: list[StudentOrm]
    groups: list[GroupOrm]

class StudentAndGroup(BaseModel):
    name: str
    group: str

class PostStudentWithGroupResponse(BaseModel):
    info: Optional[list[StudentAndGroup]]
