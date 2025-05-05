import requests, uvicorn

from fastapi import FastAPI
from config import settings

from models import (
    GetStudentList
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

@app.get
def student_with_groups_list():
    students = requests.get(f"{settings.URL}/students/get")
    groups = requests.get(f"{settings.URL}/groups/get")
    return requests.post(students, groups)

@app.post
def change_stud_name(

):
    pass

if __name__ == '__main__':
    uvicorn.run(app, port=8000)