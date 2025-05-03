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