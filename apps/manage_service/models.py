import datetime

from pydantic import BaseModel

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
