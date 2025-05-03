from pydantic import BaseModel

class Student(BaseModel):
    id: int
    name: str
    group_id: int

class GetStudentList(BaseModel):
    pass