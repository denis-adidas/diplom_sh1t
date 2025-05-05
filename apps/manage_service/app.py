import requests, uvicorn

from fastapi import FastAPI
from config import settings

from models import (
    GetStudentList, PostStudentWithGroupsRequest, StudentOrm
)

app = FastAPI(title="Manage Service")

@app.get("/")
def status_index():
    return {
        "message" : "success"
    }

@app.get("/get/students")
def test():
    response = requests.get(f"{settings.URL}/students/get") #todo костыль😭
    return GetStudentList(**response.json())

@app.get("/get/stud_info")
def student_with_groups_list():
    students = requests.get(f"{settings.DATA_URL}/students/get")
    groups = requests.get(f"{settings.DATA_URL}/groups/get")

    payload = PostStudentWithGroupsRequest(
        students=students.json()["students"],
        groups=groups.json()["groups"]
    )

    response = requests.post(
        url=f"{settings.BUSSINESS_URL}/post/student_group",
        json=payload.model_dump(exclude_none=True)
    )

    return response.json()


if __name__ == '__main__':
    uvicorn.run(app, port=8000)