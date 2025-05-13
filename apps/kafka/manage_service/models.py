import datetime

from pydantic import BaseModel, model_validator
from typing import Optional

class Student(BaseModel):
    id: int
    name: str
    group_id: int

class Group(BaseModel):
    id: int
    name: str

class GetStudentList(BaseModel):
    students: list[Student]

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

class PostCreateStudent(BaseModel):
    name: str
    group_id: Optional[int] = None
    group_name: Optional[str] = None

    @model_validator(mode="after")
    def check_param(self):
        if self.group_id is None and self.group_name is None:
            raise ValueError("group_id or group_name should be")
        return self

class PostCreateStudentWithGroups(BaseModel):
    name: str
    group_id: Optional[int] = None
    group_name: Optional[str] = None
    groups_list: list[GroupOrm]

    @model_validator(mode="after")
    def check_param(self):
        if self.group_id is None and self.group_name is None:
            raise ValueError("group_id or group_name should be")

        return self

class CreateUser(BaseModel):
    group_id: int
    name: str